"""
Suspect proposal, supervisor review, interrogation, arrest order, high-priority listing.
"""
from django.db import transaction
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.contrib.auth import get_user_model

from .models import Suspect, Interrogation, ArrestOrder
from .serializers import (
    SuspectListSerializer,
    SuspectDetailSerializer,
    SuspectProposeSerializer,
    SuspectSupervisorReviewSerializer,
    InterrogationSerializer,
    InterrogationCreateSerializer,
    InterrogationCaptainDecisionSerializer,
    InterrogationChiefReviewSerializer,
    ArrestOrderSerializer,
)
from accounts.permissions import IsDetective, IsSupervisor, IsCaptain, IsPoliceChief
from core.utils import log_audit, notify

User = get_user_model()


class SuspectListCreateView(generics.ListCreateAPIView):
    """List suspects (filter by case); detective proposes suspect."""
    permission_classes = [IsAuthenticated]
    serializer_class = SuspectListSerializer

    def get_queryset(self):
        qs = Suspect.objects.all()
        case_id = self.request.query_params.get('case')
        if case_id:
            qs = qs.filter(case_id=case_id)
        return qs.order_by('-marked_at')

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return SuspectProposeSerializer
        return SuspectListSerializer

    def post(self, request, *args, **kwargs):
        if not request.user.has_role('Detective'):
            return Response(
                {'success': False, 'error': {'message': 'Only Detective can propose suspects.'}},
                status=status.HTTP_403_FORBIDDEN,
            )
        ser = SuspectProposeSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        from cases.models import Case
        case = get_object_or_404(Case, pk=ser.validated_data['case_id'])
        user = get_object_or_404(User, pk=ser.validated_data['user_id'])
        suspect, created = Suspect.objects.get_or_create(
            case=case,
            user=user,
            defaults={
                'status': Suspect.STATUS_UNDER_PURSUIT,
                'proposed_by_detective': request.user,
            },
        )
        if not created:
            return Response(
                {'success': False, 'error': {'message': 'Already a suspect in this case.'}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        log_audit(request.user, 'create', 'Suspect', suspect.pk, f'Suspect proposed: {user.username}')
        for u in User.objects.filter(roles__name='Sergeant'):
            notify(u, 'New suspect proposed', f'Case #{case.pk}', 'suspect_proposed', 'Suspect', suspect.pk)
        return Response({'success': True, 'data': SuspectDetailSerializer(suspect).data}, status=status.HTTP_201_CREATED)


class SuspectDetailView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Suspect.objects.all()
    serializer_class = SuspectDetailSerializer


class SuspectSupervisorReviewView(APIView):
    """Sergeant approves (arrest starts) or rejects suspect."""
    permission_classes = [IsAuthenticated, IsSupervisor]

    def post(self, request, pk):
        suspect = get_object_or_404(Suspect, pk=pk)
        if suspect.approved_by_supervisor_id:
            return Response(
                {'success': False, 'error': {'message': 'Already reviewed.'}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        ser = SuspectSupervisorReviewSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        action = ser.validated_data['action']
        
        if action == 'reject':
            reason = ser.validated_data.get('reject_reason', 'No specific reason provided.')
            if suspect.proposed_by_detective_id:
                notify(
                    suspect.proposed_by_detective, 
                    'Suspect Proposal Rejected', 
                    f'Proposal for {suspect.user.username} rejected. Reason: {reason}', 
                    'suspect_rejected', 
                    'Case', 
                    suspect.case_id
                )
            suspect.delete()
            log_audit(request.user, 'reject', 'Suspect', pk, 'Suspect proposal rejected')
            return Response({'success': True, 'data': {'message': 'Suspect rejected and detective notified.'}})
        
        suspect.approved_by_supervisor = request.user
        suspect.approved_at = timezone.now()
        suspect.status = Suspect.STATUS_ARRESTED
        suspect.save()
        log_audit(request.user, 'approve', 'Suspect', suspect.pk, 'Suspect approved; arrest started')
        if suspect.case.assigned_detective_id:
            notify(suspect.case.assigned_detective, 'Suspect approved', f'Suspect arrested in case #{suspect.case_id}', 'suspect_approved', 'Suspect', suspect.pk)
        return Response({'success': True, 'data': SuspectDetailSerializer(suspect).data})


class InterrogationListCreateView(generics.ListCreateAPIView):
    """List/create interrogations. Detective and supervisor set guilt probability (1-10)."""
    permission_classes = [IsAuthenticated]
    serializer_class = InterrogationSerializer

    def get_queryset(self):
        qs = Interrogation.objects.all()
        suspect_id = self.request.query_params.get('suspect')
        if suspect_id:
            qs = qs.filter(suspect_id=suspect_id)
        return qs.order_by('-created_at')

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return InterrogationCreateSerializer
        return InterrogationSerializer


class InterrogationDetailView(generics.RetrieveUpdateAPIView):
    """Retrieve or update an interrogation (e.g., adding supervisor/detective probability later)."""
    permission_classes = [IsAuthenticated]
    queryset = Interrogation.objects.all()
    serializer_class = InterrogationCreateSerializer


class InterrogationCaptainDecisionView(APIView):
    """Captain issues final decision. For critical crimes, chief must confirm."""
    permission_classes = [IsAuthenticated, IsCaptain]

    def post(self, request, pk):
        interrogation = get_object_or_404(Interrogation, pk=pk)
        ser = InterrogationCaptainDecisionSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        interrogation.captain_decision = ser.validated_data['captain_decision']
        interrogation.captain_decided_by = request.user
        interrogation.captain_decided_at = timezone.now()
        
        case = interrogation.suspect.case
        # Require chief confirmation for CRITICAL crimes
        if case.severity == case.SEVERITY_CRISIS:
            interrogation.chief_confirmed = False
            for u in User.objects.filter(roles__name='Police Chief'):
                notify(u, 'Chief confirmation required', f'Case #{case.pk} interrogation', 'chief_confirm', 'Interrogation', interrogation.pk)
        else:
            interrogation.chief_confirmed = True
            
        interrogation.save()
        log_audit(request.user, 'update', 'Interrogation', interrogation.pk, 'Captain decision recorded')
        return Response({'success': True, 'data': InterrogationSerializer(interrogation).data})


class InterrogationChiefReviewView(APIView):
    """Police Chief confirms or rejects decision for critical crimes."""
    permission_classes = [IsAuthenticated, IsPoliceChief]

    def post(self, request, pk):
        interrogation = get_object_or_404(Interrogation, pk=pk)
        ser = InterrogationChiefReviewSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        
        action = ser.validated_data['action']
        if action == 'approve':
            interrogation.chief_confirmed = True
            log_audit(request.user, 'approve', 'Interrogation', interrogation.pk, 'Chief confirmed captain decision')
        else:
            interrogation.chief_confirmed = False
            interrogation.chief_notes = ser.validated_data.get('notes', '')
            log_audit(request.user, 'reject', 'Interrogation', interrogation.pk, 'Chief rejected captain decision')
            
        interrogation.chief_confirmed_by = request.user
        interrogation.chief_confirmed_at = timezone.now()
        interrogation.save()
        return Response({'success': True, 'data': InterrogationSerializer(interrogation).data})


class ArrestOrderListCreateView(generics.ListCreateAPIView):
    """Sergeant issues arrest/interrogation orders."""
    permission_classes = [IsAuthenticated, IsSupervisor]
    serializer_class = ArrestOrderSerializer

    def get_queryset(self):
        return ArrestOrder.objects.all().order_by('-issued_at')

    def perform_create(self, serializer):
        serializer.save(issued_by=self.request.user)


class SuspectHighPriorityListView(generics.ListAPIView):
    """Public listing: suspects with status high_priority (>1 month pursued)."""
    serializer_class = SuspectListSerializer
    permission_classes = [IsAuthenticated]  # Or AllowAny for public; spec says "public listing"

    def get_queryset(self):
        cutoff_date = timezone.now() - timezone.timedelta(days=31)
        Suspect.objects.filter(
            status=Suspect.STATUS_UNDER_PURSUIT,
            first_pursuit_date__lte=cutoff_date
        ).update(status=Suspect.STATUS_HIGH_PRIORITY)
        return Suspect.objects.filter(status=Suspect.STATUS_HIGH_PRIORITY).order_by('-first_pursuit_date')



















# """
# Suspect proposal, supervisor review, interrogation, arrest order, high-priority listing.
# """
# from rest_framework import generics, status
# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework.permissions import IsAuthenticated

# from django.shortcuts import get_object_or_404
# from django.utils import timezone
# from django.contrib.auth import get_user_model

# from .models import Suspect, Interrogation, ArrestOrder
# from .serializers import (
#     SuspectListSerializer,
#     SuspectDetailSerializer,
#     SuspectProposeSerializer,
#     SuspectSupervisorReviewSerializer,
#     InterrogationSerializer,
#     InterrogationCreateSerializer,
#     InterrogationCaptainDecisionSerializer,
#     ArrestOrderSerializer,
# )
# from accounts.permissions import IsDetective, IsSupervisor, IsCaptain, IsPoliceChief
# from core.utils import log_audit, notify

# User = get_user_model()


# class SuspectListCreateView(generics.ListCreateAPIView):
#     """List suspects (filter by case); detective proposes suspect."""
#     permission_classes = [IsAuthenticated]
#     serializer_class = SuspectListSerializer

#     def get_queryset(self):
#         qs = Suspect.objects.all()
#         case_id = self.request.query_params.get('case')
#         if case_id:
#             qs = qs.filter(case_id=case_id)
#         return qs.order_by('-marked_at')

#     def get_serializer_class(self):
#         if self.request.method == 'POST':
#             return SuspectProposeSerializer
#         return SuspectListSerializer

#     def post(self, request, *args, **kwargs):
#         if not request.user.has_role('Detective'):
#             return Response(
#                 {'success': False, 'error': {'message': 'Only Detective can propose suspects.'}},
#                 status=status.HTTP_403_FORBIDDEN,
#             )
#         ser = SuspectProposeSerializer(data=request.data)
#         ser.is_valid(raise_exception=True)
#         from cases.models import Case
#         case = get_object_or_404(Case, pk=ser.validated_data['case_id'])
#         user = get_object_or_404(User, pk=ser.validated_data['user_id'])
#         suspect, created = Suspect.objects.get_or_create(
#             case=case,
#             user=user,
#             defaults={
#                 'status': Suspect.STATUS_UNDER_PURSUIT,
#                 'proposed_by_detective': request.user,
#             },
#         )
#         if not created:
#             return Response(
#                 {'success': False, 'error': {'message': 'Already a suspect in this case.'}},
#                 status=status.HTTP_400_BAD_REQUEST,
#             )
#         log_audit(request.user, 'create', 'Suspect', suspect.pk, f'Suspect proposed: {user.username}')
#         for u in User.objects.filter(roles__name='Sergeant'):
#             notify(u, 'New suspect proposed', f'Case #{case.pk}', 'suspect_proposed', 'Suspect', suspect.pk)
#         return Response({'success': True, 'data': SuspectDetailSerializer(suspect).data}, status=status.HTTP_201_CREATED)


# class SuspectDetailView(generics.RetrieveAPIView):
#     permission_classes = [IsAuthenticated]
#     queryset = Suspect.objects.all()
#     serializer_class = SuspectDetailSerializer


# class SuspectSupervisorReviewView(APIView):
#     """Sergeant approves (arrest starts) or rejects suspect."""
#     permission_classes = [IsAuthenticated, IsSupervisor]

#     def post(self, request, pk):
#         suspect = get_object_or_404(Suspect, pk=pk)
#         if suspect.approved_by_supervisor_id:
#             return Response(
#                 {'success': False, 'error': {'message': 'Already reviewed.'}},
#                 status=status.HTTP_400_BAD_REQUEST,
#             )
#         ser = SuspectSupervisorReviewSerializer(data=request.data)
#         ser.is_valid(raise_exception=True)
#         action = ser.validated_data['action']
#         if action == 'reject':
#             suspect.delete()
#             log_audit(request.user, 'reject', 'Suspect', pk, 'Suspect proposal rejected')
#             return Response({'success': True, 'data': {'message': 'Suspect rejected.'}})
#         suspect.approved_by_supervisor = request.user
#         suspect.approved_at = timezone.now()
#         suspect.status = Suspect.STATUS_ARRESTED
#         suspect.save()
#         log_audit(request.user, 'approve', 'Suspect', suspect.pk, 'Suspect approved; arrest started')
#         if suspect.case.assigned_detective_id:
#             notify(suspect.case.assigned_detective, 'Suspect approved', f'Suspect arrested in case #{suspect.case_id}', 'suspect_approved', 'Suspect', suspect.pk)
#         return Response({'success': True, 'data': SuspectDetailSerializer(suspect).data})


# class InterrogationListCreateView(generics.ListCreateAPIView):
#     """List/create interrogations. Detective and supervisor set guilt probability (1-10)."""
#     permission_classes = [IsAuthenticated]
#     serializer_class = InterrogationSerializer

#     def get_queryset(self):
#         qs = Interrogation.objects.all()
#         suspect_id = self.request.query_params.get('suspect')
#         if suspect_id:
#             qs = qs.filter(suspect_id=suspect_id)
#         return qs.order_by('-created_at')

#     def get_serializer_class(self):
#         if self.request.method == 'POST':
#             return InterrogationCreateSerializer
#         return InterrogationSerializer


# class InterrogationCaptainDecisionView(APIView):
#     """Captain issues final decision. For critical crimes, chief must confirm."""
#     permission_classes = [IsAuthenticated, IsCaptain]

#     def post(self, request, pk):
#         interrogation = get_object_or_404(Interrogation, pk=pk)
#         ser = InterrogationCaptainDecisionSerializer(data=request.data)
#         ser.is_valid(raise_exception=True)
#         interrogation.captain_decision = ser.validated_data['captain_decision']
#         interrogation.captain_decided_by = request.user
#         interrogation.captain_decided_at = timezone.now()
#         case = interrogation.suspect.case
#         if case.severity == case.SEVERITY_CRISIS:
#             interrogation.chief_confirmed = False
#             for u in User.objects.filter(roles__name='Police Chief'):
#                 notify(u, 'Chief confirmation required', f'Case #{case.pk} interrogation', 'chief_confirm', 'Interrogation', interrogation.pk)
#         else:
#             interrogation.chief_confirmed = True
#         interrogation.save()
#         log_audit(request.user, 'update', 'Interrogation', interrogation.pk, 'Captain decision recorded')
#         return Response({'success': True, 'data': InterrogationSerializer(interrogation).data})


# class InterrogationChiefConfirmView(APIView):
#     """Police Chief confirms for critical crimes."""
#     permission_classes = [IsAuthenticated, IsPoliceChief]

#     def post(self, request, pk):
#         interrogation = get_object_or_404(Interrogation, pk=pk)
#         interrogation.chief_confirmed = True
#         interrogation.chief_confirmed_by = request.user
#         interrogation.chief_confirmed_at = timezone.now()
#         interrogation.save()
#         log_audit(request.user, 'approve', 'Interrogation', interrogation.pk, 'Chief confirmed')
#         return Response({'success': True, 'data': InterrogationSerializer(interrogation).data})


# class ArrestOrderListCreateView(generics.ListCreateAPIView):
#     """Sergeant issues arrest/interrogation orders."""
#     permission_classes = [IsAuthenticated, IsSupervisor]
#     serializer_class = ArrestOrderSerializer

#     def get_queryset(self):
#         return ArrestOrder.objects.all().order_by('-issued_at')

#     def perform_create(self, serializer):
#         serializer.save(issued_by=self.request.user)


# class SuspectHighPriorityListView(generics.ListAPIView):
#     """Public listing: suspects with status high_priority (>1 month pursued)."""
#     serializer_class = SuspectListSerializer
#     permission_classes = [IsAuthenticated]  # Or AllowAny for public; spec says "public listing"

#     def get_queryset(self):
#         qs = Suspect.objects.filter(status=Suspect.STATUS_HIGH_PRIORITY)
#         for s in Suspect.objects.filter(status=Suspect.STATUS_UNDER_PURSUIT):
#             s.update_high_priority()
#         return Suspect.objects.filter(status=Suspect.STATUS_HIGH_PRIORITY).order_by('-first_pursuit_date')
