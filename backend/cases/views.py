from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.contrib.auth import get_user_model

from .models import Case, Complaint, CaseComplainant, CrimeSceneReport
from .serializers import (
    CaseListSerializer,
    CaseDetailSerializer,
    CaseCreateUpdateSerializer,
    ComplaintListSerializer,
    ComplaintDetailSerializer,
    ComplaintCreateSerializer,
    ComplaintCorrectSerializer,
    ComplaintTraineeReviewSerializer,
    ComplaintOfficerReviewSerializer,
    CaseComplainantSerializer,
    CaseComplainantCreateSerializer,
    CrimeSceneReportSerializer,
    CrimeSceneReportCreateSerializer,
)
from accounts.permissions import (
    IsTraineeOrAbove,
    IsOfficerOrAbove,
    IsPoliceOfficer,
    IsIntern,
    IsSupervisor,
    has_any_role,
)
from core.utils import log_audit, notify

User = get_user_model()


class CaseListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated, IsOfficerOrAbove]
    serializer_class = CaseListSerializer

    def get_queryset(self):
        qs = Case.objects.all()
        if not has_any_role(self.request.user, ['System Administrator', 'Police Chief', 'Captain', 'Sergeant']):
            qs = qs.filter(assigned_detective=self.request.user) | qs.filter(created_by=self.request.user)
        return qs.distinct().order_by('-created_at')

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CaseCreateUpdateSerializer
        return CaseListSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
        log_audit(
            self.request.user, 'create', 'Case', serializer.instance.pk,
            f'Case created: {serializer.instance.title}',
        )


class CaseDetailView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated, IsOfficerOrAbove]
    queryset = Case.objects.all()
    serializer_class = CaseDetailSerializer

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return CaseCreateUpdateSerializer
        return CaseDetailSerializer


class ComplaintListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ComplaintListSerializer

    def get_queryset(self):
        user = self.request.user
        if user.has_role('Complainant / Witness') or not has_any_role(user, [
            'Intern', 'Police Officer', 'Detective', 'Sergeant', 'Captain', 'Police Chief', 'System Administrator',
        ]):
            return Complaint.objects.filter(complainant=user).order_by('-created_at')
        return Complaint.objects.all().order_by('-created_at')

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ComplaintCreateSerializer
        return ComplaintListSerializer

    def perform_create(self, serializer):
        c = serializer.save()
        log_audit(self.request.user, 'create', 'Complaint', c.pk, f'Complaint submitted: {c.title}')
        
        for u in User.objects.filter(roles__name='Intern'):
            notify(u, 'New complaint to review', c.title, 'complaint_pending_trainee', 'Complaint', c.pk)


class ComplaintDetailView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Complaint.objects.all()
    serializer_class = ComplaintDetailSerializer


class ComplaintCorrectView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        complaint = get_object_or_404(Complaint, pk=pk, complainant=request.user)
        if complaint.status != Complaint.STATUS_CORRECTION_NEEDED:
            return Response(
                {'success': False, 'error': {'message': 'Complaint is not in correction state.'}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        ser = ComplaintCorrectSerializer(data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        
        if ser.validated_data.get('title'):
            complaint.title = ser.validated_data['title']
        if ser.validated_data.get('description'):
            complaint.description = ser.validated_data['description']
            
        complaint.correction_count += 1
        complaint.last_correction_message = ''
        
        if complaint.correction_count >= 3:
            complaint.status = Complaint.STATUS_REJECTED
            complaint.save()
            log_audit(request.user, 'reject', 'Complaint', complaint.pk, 'Complaint rejected after 3 corrections')
            return Response({'success': True, 'data': {'status': complaint.status, 'message': 'Complaint rejected after 3 failed corrections.'}})
            
        complaint.status = Complaint.STATUS_PENDING_TRAINEE
        complaint.save()
        log_audit(request.user, 'update', 'Complaint', complaint.pk, 'Complaint resubmitted for correction')
        return Response({'success': True, 'data': ComplaintDetailSerializer(complaint).data})


class ComplaintTraineeReviewView(APIView):
    permission_classes = [IsAuthenticated, IsIntern]

    def post(self, request, pk):
        complaint = get_object_or_404(Complaint, pk=pk)
        if complaint.status != Complaint.STATUS_PENDING_TRAINEE:
            return Response(
                {'success': False, 'error': {'message': 'Complaint not pending trainee review.'}},
                status=status.HTTP_400_BAD_REQUEST,
            )
            
        ser = ComplaintTraineeReviewSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        action = ser.validated_data['action']
        
        if action == 'return_correction':
            complaint.status = Complaint.STATUS_CORRECTION_NEEDED
            complaint.last_correction_message = ser.validated_data.get('correction_message', '')
            complaint.reviewed_by_trainee = request.user
            complaint.save()
            notify(complaint.complainant, 'Complaint needs correction', complaint.last_correction_message, 'complaint_correction', 'Complaint', complaint.pk)
            log_audit(request.user, 'update', 'Complaint', complaint.pk, 'Returned for correction')
        else:
            complaint.status = Complaint.STATUS_PENDING_OFFICER
            complaint.reviewed_by_trainee = request.user
            complaint.save()
            for u in User.objects.filter(roles__name='Police Officer'):
                notify(u, 'Complaint pending approval', complaint.title, 'complaint_pending_officer', 'Complaint', complaint.pk)
            log_audit(request.user, 'approve', 'Complaint', complaint.pk, 'Forwarded to officer')
            
        return Response({'success': True, 'data': ComplaintDetailSerializer(complaint).data})


class ComplaintOfficerReviewView(APIView):
    permission_classes = [IsAuthenticated, IsPoliceOfficer]

    def post(self, request, pk):
        complaint = get_object_or_404(Complaint, pk=pk)
        if complaint.status != Complaint.STATUS_PENDING_OFFICER:
            return Response(
                {'success': False, 'error': {'message': 'Complaint not pending officer approval.'}},
                status=status.HTTP_400_BAD_REQUEST,
            )
            
        ser = ComplaintOfficerReviewSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        action = ser.validated_data['action']
        
        if action == 'send_back':
            complaint.status = Complaint.STATUS_PENDING_TRAINEE
            complaint.reviewed_by_officer = None
            complaint.save()
            log_audit(request.user, 'update', 'Complaint', complaint.pk, 'Sent back to trainee')
        else:
            case = Case.objects.create(
                title=complaint.title,
                description=complaint.description,
                severity=Case.SEVERITY_LEVEL_3,
                status=Case.STATUS_OPEN,
                is_crime_scene_case=False,
                created_by=request.user,
            )
            complaint.case = case
            complaint.status = Complaint.STATUS_APPROVED
            complaint.reviewed_by_officer = request.user
            complaint.save()
            CaseComplainant.objects.create(case=case, user=complaint.complainant, is_primary=True)
            log_audit(request.user, 'approve', 'Complaint', complaint.pk, f'Approved; Case #{case.pk} created')
            notify(complaint.complainant, 'Complaint approved', f'Case #{case.pk} created.', 'complaint_approved', 'Case', case.pk)
            
        return Response({'success': True, 'data': ComplaintDetailSerializer(complaint).data})


class CrimeSceneReportListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated, IsOfficerOrAbove]
    serializer_class = CrimeSceneReportSerializer

    def get_queryset(self):
        return CrimeSceneReport.objects.all().order_by('-created_at')

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CrimeSceneReportCreateSerializer
        return CrimeSceneReportSerializer

    def perform_create(self, serializer):
        report = serializer.save(reported_by=self.request.user)
        case = report.case
        case.is_crime_scene_case = True
        
        if self.request.user.has_role('Police Chief'):
            report.approved_by_supervisor = self.request.user
            report.approved_at = timezone.now()
            report.save()
            case.status = Case.STATUS_OPEN
        else:
            case.status = Case.STATUS_PENDING_APPROVAL
            for u in User.objects.filter(roles__name='Sergeant'):
                notify(u, 'Crime scene report pending approval', str(case), 'crime_scene_pending', 'CrimeSceneReport', report.pk)
                
        case.save()
        log_audit(self.request.user, 'create', 'CrimeSceneReport', report.pk, f'Crime scene report for case #{case.pk}')


class CrimeSceneReportApproveView(APIView):
    permission_classes = [IsAuthenticated, IsSupervisor]

    def post(self, request, pk):
        report = get_object_or_404(CrimeSceneReport, pk=pk)
        if report.approved_by_supervisor_id:
            return Response(
                {'success': False, 'error': {'message': 'Already approved.'}},
                status=status.HTTP_400_BAD_REQUEST,
            )
            
        report.approved_by_supervisor = request.user
        report.approved_at = timezone.now()
        report.save()
        
        case = report.case
        case.status = Case.STATUS_OPEN
        case.save()
        
        log_audit(request.user, 'approve', 'CrimeSceneReport', report.pk, 'Approved')
        return Response({'success': True, 'data': CrimeSceneReportSerializer(report).data})


class CaseComplainantListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated, IsOfficerOrAbove]
    serializer_class = CaseComplainantSerializer

    def get_queryset(self):
        case_id = self.kwargs.get('case_pk')
        return CaseComplainant.objects.filter(case_id=case_id)

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CaseComplainantCreateSerializer
        return CaseComplainantSerializer

    def perform_create(self, serializer):
        serializer.save(case_id=self.kwargs['case_pk'])



















# """
# Case, Complaint, CrimeScene API. Workflow: trainee review -> officer approval; crime scene approval.
# """
# from rest_framework import generics, status
# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework.permissions import IsAuthenticated

# from django.shortcuts import get_object_or_404

# from .models import Case, Complaint, CaseComplainant, CrimeSceneReport
# from .serializers import (
#     CaseListSerializer,
#     CaseDetailSerializer,
#     CaseCreateUpdateSerializer,
#     ComplaintListSerializer,
#     ComplaintDetailSerializer,
#     ComplaintCreateSerializer,
#     ComplaintCorrectSerializer,
#     ComplaintTraineeReviewSerializer,
#     ComplaintOfficerReviewSerializer,
#     CaseComplainantSerializer,
#     CaseComplainantCreateSerializer,
#     CrimeSceneReportSerializer,
#     CrimeSceneReportCreateSerializer,
# )
# from accounts.permissions import (
#     IsTraineeOrAbove,
#     IsOfficerOrAbove,
#     IsPoliceOfficer,
#     IsIntern,
#     IsSupervisor,
#     has_any_role,
# )
# from core.utils import log_audit, notify


# class CaseListCreateView(generics.ListCreateAPIView):
#     """List cases; create case (officer/admin after complaint approved or crime scene)."""
#     permission_classes = [IsAuthenticated, IsOfficerOrAbove]
#     serializer_class = CaseListSerializer

#     def get_queryset(self):
#         qs = Case.objects.all()
#         if not has_any_role(self.request.user, ['System Administrator', 'Police Chief', 'Captain', 'Sergeant']):
#             qs = qs.filter(assigned_detective=self.request.user) | qs.filter(created_by=self.request.user)
#         return qs.distinct().order_by('-created_at')

#     def get_serializer_class(self):
#         if self.request.method == 'POST':
#             return CaseCreateUpdateSerializer
#         return CaseListSerializer

#     def perform_create(self, serializer):
#         serializer.save(created_by=self.request.user)
#         log_audit(
#             self.request.user, 'create', 'Case', serializer.instance.pk,
#             f'Case created: {serializer.instance.title}',
#         )


# class CaseDetailView(generics.RetrieveUpdateAPIView):
#     """Retrieve/update case. Detective/supervisor can update assigned_detective, status."""
#     permission_classes = [IsAuthenticated, IsOfficerOrAbove]
#     queryset = Case.objects.all()
#     serializer_class = CaseDetailSerializer

#     def get_serializer_class(self):
#         if self.request.method in ('PUT', 'PATCH'):
#             return CaseCreateUpdateSerializer
#         return CaseDetailSerializer


# class ComplaintListCreateView(generics.ListCreateAPIView):
#     """List complaints (filtered by role); complainant creates complaint."""
#     permission_classes = [IsAuthenticated]
#     serializer_class = ComplaintListSerializer

#     def get_queryset(self):
#         user = self.request.user
#         if user.has_role('Complainant / Witness') or not has_any_role(user, [
#             'Intern', 'Police Officer', 'Detective', 'Sergeant', 'Captain', 'Police Chief', 'System Administrator',
#         ]):
#             return Complaint.objects.filter(complainant=user).order_by('-created_at')
#         return Complaint.objects.all().order_by('-created_at')

#     def get_serializer_class(self):
#         if self.request.method == 'POST':
#             return ComplaintCreateSerializer
#         return ComplaintListSerializer

#     def perform_create(self, serializer):
#         c = serializer.save()
#         log_audit(self.request.user, 'create', 'Complaint', c.pk, f'Complaint submitted: {c.title}')
#         # Notify trainees for review
#         from django.contrib.auth import get_user_model
#         for u in get_user_model().objects.filter(roles__name='Intern'):
#             notify(u, 'New complaint to review', c.title, 'complaint_pending_trainee', 'Complaint', c.pk)


# class ComplaintDetailView(generics.RetrieveAPIView):
#     permission_classes = [IsAuthenticated]
#     queryset = Complaint.objects.all()
#     serializer_class = ComplaintDetailSerializer


# class ComplaintCorrectView(APIView):
#     """Complainant resubmits after correction. After 3 failures, case rejected."""
#     permission_classes = [IsAuthenticated]

#     def post(self, request, pk):
#         complaint = get_object_or_404(Complaint, pk=pk, complainant=request.user)
#         if complaint.status != Complaint.STATUS_CORRECTION_NEEDED:
#             return Response(
#                 {'success': False, 'error': {'message': 'Complaint is not in correction state.'}},
#                 status=status.HTTP_400_BAD_REQUEST,
#             )
#         ser = ComplaintCorrectSerializer(data=request.data, partial=True)
#         ser.is_valid(raise_exception=True)
#         if ser.validated_data.get('title'):
#             complaint.title = ser.validated_data['title']
#         if ser.validated_data.get('description'):
#             complaint.description = ser.validated_data['description']
#         complaint.correction_count += 1
#         complaint.last_correction_message = ''
#         if complaint.correction_count >= 3:
#             complaint.status = Complaint.STATUS_REJECTED
#             complaint.save()
#             log_audit(request.user, 'reject', 'Complaint', complaint.pk, 'Complaint rejected after 3 corrections')
#             return Response({'success': True, 'data': {'status': complaint.status, 'message': 'Complaint rejected after 3 failed corrections.'}})
#         complaint.status = Complaint.STATUS_PENDING_TRAINEE
#         complaint.save()
#         log_audit(request.user, 'update', 'Complaint', complaint.pk, 'Complaint resubmitted for correction')
#         return Response({'success': True, 'data': ComplaintDetailSerializer(complaint).data})


# class ComplaintTraineeReviewView(APIView):
#     """Intern: approve (forward to officer) or return for correction with message."""
#     permission_classes = [IsAuthenticated, IsIntern]

#     def post(self, request, pk):
#         complaint = get_object_or_404(Complaint, pk=pk)
#         if complaint.status != Complaint.STATUS_PENDING_TRAINEE:
#             return Response(
#                 {'success': False, 'error': {'message': 'Complaint not pending trainee review.'}},
#                 status=status.HTTP_400_BAD_REQUEST,
#             )
#         ser = ComplaintTraineeReviewSerializer(data=request.data)
#         ser.is_valid(raise_exception=True)
#         action = ser.validated_data['action']
#         if action == 'return_correction':
#             complaint.status = Complaint.STATUS_CORRECTION_NEEDED
#             complaint.last_correction_message = ser.validated_data.get('correction_message', '')
#             complaint.reviewed_by_trainee = request.user
#             complaint.save()
#             notify(complaint.complainant, 'Complaint needs correction', complaint.last_correction_message, 'complaint_correction', 'Complaint', complaint.pk)
#             log_audit(request.user, 'update', 'Complaint', complaint.pk, 'Returned for correction')
#         else:
#             complaint.status = Complaint.STATUS_PENDING_OFFICER
#             complaint.reviewed_by_trainee = request.user
#             complaint.save()
#             # Notify officers
#             from django.contrib.auth import get_user_model
#             for u in get_user_model().objects.filter(roles__name='Police Officer'):
#                 notify(u, 'Complaint pending approval', complaint.title, 'complaint_pending_officer', 'Complaint', complaint.pk)
#             log_audit(request.user, 'approve', 'Complaint', complaint.pk, 'Forwarded to officer')
#         return Response({'success': True, 'data': ComplaintDetailSerializer(complaint).data})


# class ComplaintOfficerReviewView(APIView):
#     """Officer: approve (create case + add complainant) or send back to trainee."""
#     permission_classes = [IsAuthenticated, IsPoliceOfficer]

#     def post(self, request, pk):
#         complaint = get_object_or_404(Complaint, pk=pk)
#         if complaint.status != Complaint.STATUS_PENDING_OFFICER:
#             return Response(
#                 {'success': False, 'error': {'message': 'Complaint not pending officer approval.'}},
#                 status=status.HTTP_400_BAD_REQUEST,
#             )
#         ser = ComplaintOfficerReviewSerializer(data=request.data)
#         ser.is_valid(raise_exception=True)
#         action = ser.validated_data['action']
#         if action == 'send_back':
#             complaint.status = Complaint.STATUS_PENDING_TRAINEE
#             complaint.reviewed_by_officer = None
#             complaint.save()
#             log_audit(request.user, 'update', 'Complaint', complaint.pk, 'Sent back to trainee')
#         else:
#             case = Case.objects.create(
#                 title=complaint.title,
#                 description=complaint.description,
#                 severity=Case.SEVERITY_LEVEL_3,
#                 status=Case.STATUS_OPEN,
#                 is_crime_scene_case=False,
#                 created_by=request.user,
#             )
#             complaint.case = case
#             complaint.status = Complaint.STATUS_APPROVED
#             complaint.reviewed_by_officer = request.user
#             complaint.save()
#             CaseComplainant.objects.create(case=case, user=complaint.complainant, is_primary=True)
#             log_audit(request.user, 'approve', 'Complaint', complaint.pk, f'Approved; Case #{case.pk} created')
#             notify(complaint.complainant, 'Complaint approved', f'Case #{case.pk} created.', 'complaint_approved', 'Case', case.pk)
#         return Response({'success': True, 'data': ComplaintDetailSerializer(complaint).data})


# class CrimeSceneReportListCreateView(generics.ListCreateAPIView):
#     """Create crime scene report (officer). Requires supervisor approval unless chief."""
#     permission_classes = [IsAuthenticated, IsOfficerOrAbove]
#     serializer_class = CrimeSceneReportSerializer

#     def get_queryset(self):
#         return CrimeSceneReport.objects.all().order_by('-created_at')

#     def get_serializer_class(self):
#         if self.request.method == 'POST':
#             return CrimeSceneReportCreateSerializer
#         return CrimeSceneReportSerializer

#     def perform_create(self, serializer):
#         case = serializer.validated_data['case']
#         if case.is_crime_scene_case:
#             report = serializer.save(reported_by=self.request.user)
#         else:
#             report = serializer.save(reported_by=self.request.user)
#         log_audit(self.request.user, 'create', 'CrimeSceneReport', report.pk, f'Crime scene report for case #{case.pk}')
#         if self.request.user.has_role('Police Chief'):
#             report.approved_by_supervisor = self.request.user
#             from django.utils import timezone
#             report.approved_at = timezone.now()
#             report.save()
#         else:
#             from django.contrib.auth import get_user_model
#             for u in get_user_model().objects.filter(roles__name='Sergeant'):
#                 notify(u, 'Crime scene report pending approval', str(case), 'crime_scene_pending', 'CrimeSceneReport', report.pk)


# class CrimeSceneReportApproveView(APIView):
#     """Supervisor approves crime scene report."""
#     permission_classes = [IsAuthenticated, IsSupervisor]

#     def post(self, request, pk):
#         report = get_object_or_404(CrimeSceneReport, pk=pk)
#         if report.approved_by_supervisor_id:
#             return Response(
#                 {'success': False, 'error': {'message': 'Already approved.'}},
#                 status=status.HTTP_400_BAD_REQUEST,
#             )
#         from django.utils import timezone
#         report.approved_by_supervisor = request.user
#         report.approved_at = timezone.now()
#         report.save()
#         log_audit(request.user, 'approve', 'CrimeSceneReport', report.pk, 'Approved')
#         return Response({'success': True, 'data': CrimeSceneReportSerializer(report).data})


# class CaseComplainantListCreateView(generics.ListCreateAPIView):
#     """List/add complainants to a case (multiple complainants supported)."""
#     permission_classes = [IsAuthenticated, IsOfficerOrAbove]
#     serializer_class = CaseComplainantSerializer

#     def get_queryset(self):
#         case_id = self.kwargs.get('case_pk')
#         return CaseComplainant.objects.filter(case_id=case_id)

#     def get_serializer_class(self):
#         if self.request.method == 'POST':
#             return CaseComplainantCreateSerializer
#         return CaseComplainantSerializer

#     def perform_create(self, serializer):
#         serializer.save(case_id=self.kwargs['case_pk'])
