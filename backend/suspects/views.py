from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny

from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.contrib.auth import get_user_model

from .models import Suspect, Interrogation, ArrestOrder, CaptainDecision, ChiefApproval
from cases.models import Case
from .serializers import (
    SuspectListSerializer,
    SuspectDetailSerializer,
    SuspectProposeSerializer,
    SuspectSupervisorReviewSerializer,
    MostWantedPublicSerializer,
    InterrogationSerializer,
    InterrogationCreateSerializer,
    InterrogationCaptainDecisionSerializer,
    InterrogationSubmitScoreSerializer,
    CaptainDecisionSerializer,
    CaptainDecisionCreateSerializer,
    ChiefApprovalSerializer,
    ChiefApprovalCreateSerializer,
    ArrestOrderSerializer,
)
from accounts.permissions import IsDetective, IsSupervisor, IsCaptain, IsPoliceChief
from core.utils import log_audit, notify
from cases.models import Case

User = get_user_model()


def _maybe_clear_waiting_sergeant(case):
    """If case is WAITING_SERGEANT_APPROVAL and no suspects left pending sergeant review, set back to under_investigation."""
    if case.status != Case.STATUS_WAITING_SERGEANT_APPROVAL:
        return
    pending = case.suspects.filter(
        approved_by_supervisor__isnull=True,
        status=Suspect.STATUS_UNDER_INVESTIGATION,
    ).exists()
    if not pending:
        case.status = Case.STATUS_UNDER_INVESTIGATION
        case.save(update_fields=['status', 'updated_at'])


class SuspectListCreateView(generics.ListCreateAPIView):
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
                {'success': False, 'error': {'message': 'Forbidden'}},
                status=status.HTTP_403_FORBIDDEN,
            )
        ser = SuspectProposeSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        case = get_object_or_404(Case, pk=ser.validated_data['case_id'])
        user = get_object_or_404(User, pk=ser.validated_data['user_id'])
        suspect, created = Suspect.objects.get_or_create(
            case=case,
            user=user,
            defaults={
                'status': Suspect.STATUS_UNDER_INVESTIGATION,
                'proposed_by_detective': request.user,
            },
        )
        if not created:
            return Response(
                {'success': False, 'error': {'message': 'Exists'}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        log_audit(request.user, 'create', 'Suspect', suspect.pk, 'Proposed')
        for u in User.objects.filter(roles__name='Sergeant'):
            notify(u, 'Proposed', f'{case.pk}', 'suspect_proposed', 'Suspect', suspect.pk)
        return Response({'success': True, 'data': SuspectDetailSerializer(suspect).data}, status=status.HTTP_201_CREATED)


class SuspectDetailView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Suspect.objects.all()
    serializer_class = SuspectDetailSerializer


class SuspectSupervisorReviewView(APIView):
    """Sergeant approves (arrest starts) or rejects suspect. Rejection notifies detective; case remains open."""
    permission_classes = [IsAuthenticated, IsSupervisor]

    def post(self, request, pk):
        suspect = get_object_or_404(Suspect, pk=pk)
        if suspect.approved_by_supervisor_id or suspect.status == Suspect.STATUS_REJECTED:
            return Response(
                {'success': False, 'error': {'message': 'Reviewed'}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        ser = SuspectSupervisorReviewSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        action = ser.validated_data['action']
        if action == 'reject':
            msg = ser.validated_data.get('rejection_message', '') or 'Suspect proposal rejected by sergeant.'
            suspect.status = Suspect.STATUS_REJECTED
            suspect.rejection_message = msg
            suspect.approved_by_supervisor = None
            suspect.save(update_fields=['status', 'rejection_message', 'approved_by_supervisor'])
            log_audit(request.user, 'reject', 'Suspect', suspect.pk, 'Suspect rejected by sergeant')
            if suspect.case.assigned_detective_id:
                notify(
                    suspect.case.assigned_detective,
                    'Suspect rejected',
                    f'Case #{suspect.case_id}: {msg}',
                    'suspect_rejected',
                    'Suspect',
                    suspect.pk,
                )
            _maybe_clear_waiting_sergeant(suspect.case)
            return Response({'success': True, 'data': SuspectDetailSerializer(suspect).data})
        suspect.approved_by_supervisor = request.user
        suspect.approved_at = timezone.now()
        suspect.status = Suspect.STATUS_ARRESTED
        suspect.save()
        log_audit(request.user, 'approve', 'Suspect', suspect.pk, 'Approved')
        if suspect.case.assigned_detective_id:
            notify(
                suspect.case.assigned_detective,
                'Suspect approved',
                f'Suspect arrested in case #{suspect.case_id}. Arrest process begins.',
                'suspect_approved',
                'Suspect',
                suspect.pk,
            )
        _maybe_clear_waiting_sergeant(suspect.case)
        return Response({'success': True, 'data': SuspectDetailSerializer(suspect).data})


class InterrogationListCreateView(generics.ListCreateAPIView):
    """List/create interrogations. Create creates record; use submit-detective-score/submit-sergeant-score for scores."""
    permission_classes = [IsAuthenticated]
    serializer_class = InterrogationSerializer

    def get_queryset(self):
        qs = Interrogation.objects.select_related('suspect', 'suspect__case')
        suspect_id = self.request.query_params.get('suspect')
        case_id = self.request.query_params.get('case')
        if suspect_id:
            qs = qs.filter(suspect_id=suspect_id)
        if case_id:
            qs = qs.filter(suspect__case_id=case_id)
        return qs.order_by('-created_at')

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return InterrogationCreateSerializer
        return InterrogationSerializer


def _notify_captain_when_both_scores(interrogation):
    """When both detective and supervisor scores exist, notify captain."""
    if interrogation.detective_probability is not None and interrogation.supervisor_probability is not None:
        for u in User.objects.filter(roles__name='Captain'):
            notify(
                u,
                'Interrogation scores ready',
                f'Case #{interrogation.suspect.case_id} suspect ready for captain decision.',
                'interrogation_ready',
                'Interrogation',
                interrogation.pk,
            )


class InterrogationSubmitDetectiveScoreView(APIView):
    """Only the detective assigned to the case can submit detective guilt score (1-10). One score per suspect."""
    permission_classes = [IsAuthenticated, IsDetective]

    def post(self, request, pk):
        interrogation = get_object_or_404(Interrogation, pk=pk)
        case = interrogation.suspect.case
        if case.assigned_detective_id != request.user.id:
            return Response(
                {'success': False, 'error': {'message': 'Only the detective assigned to this case can submit the detective score.'}},
                status=status.HTTP_403_FORBIDDEN,
            )
        if interrogation.detective_probability is not None:
            return Response(
                {'success': False, 'error': {'message': 'Detective score already submitted for this suspect.'}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        ser = InterrogationSubmitScoreSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        interrogation.detective_probability = ser.validated_data['guilt_score']
        if ser.validated_data.get('notes'):
            interrogation.notes = (interrogation.notes or '') + (' Detective: ' + ser.validated_data['notes'])
        interrogation.save(update_fields=['detective_probability', 'notes', 'updated_at'])
        log_audit(request.user, 'update', 'Interrogation', interrogation.pk, f'Detective score {interrogation.detective_probability} submitted')
        _notify_captain_when_both_scores(interrogation)
        return Response({'success': True, 'data': InterrogationSerializer(interrogation).data})


class InterrogationSubmitSergeantScoreView(APIView):
    """Only a Sergeant can submit sergeant guilt score (1-10). One score per suspect."""
    permission_classes = [IsAuthenticated, IsSupervisor]

    def post(self, request, pk):
        interrogation = get_object_or_404(Interrogation, pk=pk)
        if interrogation.supervisor_probability is not None:
            return Response(
                {'success': False, 'error': {'message': 'Sergeant score already submitted for this suspect.'}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        ser = InterrogationSubmitScoreSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        interrogation.supervisor_probability = ser.validated_data['guilt_score']
        if ser.validated_data.get('notes'):
            interrogation.notes = (interrogation.notes or '') + (' Sergeant: ' + ser.validated_data['notes'])
        interrogation.save(update_fields=['supervisor_probability', 'notes', 'updated_at'])
        log_audit(request.user, 'update', 'Interrogation', interrogation.pk, f'Sergeant score {interrogation.supervisor_probability} submitted')
        _notify_captain_when_both_scores(interrogation)
        return Response({'success': True, 'data': InterrogationSerializer(interrogation).data})


class InterrogationCaptainDecisionView(APIView):
    """Captain issues final decision. If crime severity is CRITICAL (Crisis), chief must also approve."""
    permission_classes = [IsAuthenticated, IsCaptain]

    def post(self, request, pk):
        interrogation = get_object_or_404(Interrogation, pk=pk)
        ser = InterrogationCaptainDecisionSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        interrogation.captain_decision = ser.validated_data['captain_decision']
        interrogation.captain_decided_by = request.user
        interrogation.captain_decided_at = timezone.now()
        case = interrogation.suspect.case
        if case.severity == Case.SEVERITY_CRISIS:
            interrogation.chief_confirmed = False
            for u in User.objects.filter(roles__name='Police Chief'):
                notify(u, 'Confirm', f'{case.pk}', 'chief_confirm', 'Interrogation', interrogation.pk)
        else:
            interrogation.chief_confirmed = True
        interrogation.save()
        log_audit(request.user, 'update', 'Interrogation', interrogation.pk, 'Decided')
        return Response({'success': True, 'data': InterrogationSerializer(interrogation).data})


class InterrogationChiefConfirmView(APIView):
    """Police Chief confirms for critical crimes (legacy interrogation flow)."""
    permission_classes = [IsAuthenticated, IsPoliceChief]

    def post(self, request, pk):
        interrogation = get_object_or_404(Interrogation, pk=pk)
        interrogation.chief_confirmed = True
        interrogation.chief_confirmed_by = request.user
        interrogation.chief_confirmed_at = timezone.now()
        interrogation.save()
        log_audit(request.user, 'approve', 'Interrogation', interrogation.pk, 'Confirmed')
        return Response({'success': True, 'data': InterrogationSerializer(interrogation).data})


def _apply_captain_decision(captain_decision):
    """Update suspect and case status after captain decision (and chief approval if CRITICAL). If GUILTY, refer case to court (create Trial)."""
    from cases.models import Case
    from judiciary.models import Trial

    suspect = captain_decision.suspect
    case = captain_decision.case
    if captain_decision.final_decision == CaptainDecision.DECISION_GUILTY:
        suspect.status = Suspect.STATUS_ARRESTED  # remains arrested, sent to trial
        suspect.save(update_fields=['status'])
        # Send case to court: create Trial so judge can see and record verdict
        trial, created = Trial.objects.get_or_create(
            case=case,
            defaults={'suspect': suspect},
        )
        if not created and not trial.suspect_id:
            trial.suspect = suspect
            trial.save(update_fields=['suspect'])
        case.status = Case.STATUS_REFERRED_TO_JUDICIARY
        case.save(update_fields=['status', 'updated_at'])
    else:
        suspect.mark_released()
        if case.status == Case.STATUS_UNDER_INVESTIGATION:
            case.save(update_fields=['updated_at'])


class CaptainDecisionListCreateView(APIView):
    """Captain creates final decision (GUILTY/NOT_GUILTY). CRITICAL cases require chief approval before applying."""
    permission_classes = [IsAuthenticated, IsCaptain]

    def get(self, request):
        qs = CaptainDecision.objects.select_related('suspect', 'case', 'decided_by').order_by('-created_at')
        suspect_id = request.query_params.get('suspect')
        case_id = request.query_params.get('case')
        if suspect_id:
            qs = qs.filter(suspect_id=suspect_id)
        if case_id:
            qs = qs.filter(case_id=case_id)
        data = CaptainDecisionSerializer(qs, many=True).data
        return Response({'results': data})

    def post(self, request):
        ser = CaptainDecisionCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        suspect = get_object_or_404(Suspect, pk=ser.validated_data['suspect_id'])
        case = suspect.case
        if case.id != ser.validated_data['case_id']:
            return Response(
                {'success': False, 'error': {'message': 'Case does not match suspect.'}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        cap = CaptainDecision.objects.create(
            suspect=suspect,
            case=case,
            final_decision=ser.validated_data['final_decision'],
            reasoning=ser.validated_data.get('reasoning', ''),
            decided_by=request.user,
        )
        log_audit(request.user, 'create', 'CaptainDecision', cap.pk, f'Decision: {cap.final_decision}')
        if case.severity == Case.SEVERITY_CRISIS:
            for u in User.objects.filter(roles__name='Police Chief'):
                notify(u, 'Chief approval required', f'Case #{case.pk} captain decision for suspect', 'chief_approval_required', 'CaptainDecision', cap.pk)
            return Response({'success': True, 'data': CaptainDecisionSerializer(cap).data, 'requires_chief_approval': True})
        _apply_captain_decision(cap)
        return Response({'success': True, 'data': CaptainDecisionSerializer(cap).data})


class ChiefApprovalView(APIView):
    """Police Chief approves or rejects captain decision (for CRITICAL severity cases)."""
    permission_classes = [IsAuthenticated, IsPoliceChief]

    def post(self, request, pk):
        captain_decision = get_object_or_404(CaptainDecision, pk=pk)
        if getattr(captain_decision, 'chief_approval', None):
            return Response(
                {'success': False, 'error': {'message': 'Chief has already decided on this captain decision.'}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        ser = ChiefApprovalCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        approval = ChiefApproval.objects.create(
            captain_decision=captain_decision,
            status=ser.validated_data['status'],
            comment=ser.validated_data.get('comment', ''),
            approved_by=request.user,
        )
        log_audit(request.user, 'approve' if approval.status == ChiefApproval.STATUS_APPROVED else 'reject', 'ChiefApproval', approval.pk, approval.status)
        if approval.status == ChiefApproval.STATUS_APPROVED:
            _apply_captain_decision(captain_decision)
        return Response({'success': True, 'data': ChiefApprovalSerializer(approval).data})


class ArrestOrderListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated, IsSupervisor]
    serializer_class = ArrestOrderSerializer

    def get_queryset(self):
        return ArrestOrder.objects.all().order_by('-issued_at')

    def perform_create(self, serializer):
        serializer.save(issued_by=self.request.user)


class SuspectHighPriorityListView(generics.ListAPIView):
    """Dashboard listing: suspects with status most_wanted (under investigation >30 days)."""
    serializer_class = SuspectListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        for s in Suspect.objects.filter(status=Suspect.STATUS_UNDER_INVESTIGATION):
            s.update_most_wanted()
        return Suspect.objects.filter(status=Suspect.STATUS_MOST_WANTED).order_by('-first_pursuit_date')


class MostWantedPublicListView(generics.ListAPIView):
    """Public Most Wanted page: photo, personal details, ranking by score, reward = score * 20,000,000 Rials."""
    serializer_class = MostWantedPublicSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        qs = Suspect.objects.filter(status__in=(Suspect.STATUS_UNDER_INVESTIGATION, Suspect.STATUS_MOST_WANTED))
        for s in qs:
            s.update_most_wanted()
        most_wanted = Suspect.objects.filter(status=Suspect.STATUS_MOST_WANTED)
        # Sort by ranking_score descending (score = days * crime_degree)
        return sorted(most_wanted, key=lambda s: s.ranking_score(), reverse=True)
