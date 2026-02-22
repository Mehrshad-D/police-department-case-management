"""
Trial and verdict. Judge views full case and records verdict + punishment.
"""
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from django.shortcuts import get_object_or_404

from .models import Trial, Verdict
from .serializers import (
    TrialSerializer, 
    FullTrialDetailSerializer, 
    VerdictSerializer, 
    VerdictCreateSerializer
)
from accounts.permissions import IsJudge, CanReferCaseToJudiciary
from core.utils import log_audit


class TrialListCreateView(generics.ListCreateAPIView):
    """List trials; create trial when case referred to judiciary (Captain/Chief/Judge)."""
    permission_classes = [IsAuthenticated]
    serializer_class = TrialSerializer
    queryset = Trial.objects.all().order_by('-started_at')

    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsAuthenticated(), IsJudge()]
        return [IsAuthenticated(), CanReferCaseToJudiciary()]

    def perform_create(self, serializer):
        judge = self.request.user if self.request.user.has_role('Judge') else None
        trial = serializer.save(judge=judge)
        trial.case.status = trial.case.STATUS_REFERRED_TO_JUDICIARY
        trial.case.save(update_fields=['status'])


class TrialDetailView(generics.RetrieveUpdateAPIView):
    """Judge views full case history, reports, approvals, officers, evidence (via case context)."""
    permission_classes = [IsAuthenticated, IsJudge]
    queryset = Trial.objects.all()
    serializer_class = FullTrialDetailSerializer


class VerdictListCreateView(generics.ListCreateAPIView):
    """List verdicts; judge records verdict + punishment and auto-closes the case."""
    permission_classes = [IsAuthenticated, IsJudge]
    serializer_class = VerdictSerializer

    def get_queryset(self):
        return Verdict.objects.all().order_by('-recorded_at')

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return VerdictCreateSerializer
        return VerdictSerializer

    def perform_create(self, serializer):
        # 1. Save the verdict
        verdict = serializer.save(recorded_by=self.request.user)
        
        # 2. Close the Trial
        trial = verdict.trial
        trial.closed_at = timezone.now()
        trial.save(update_fields=['closed_at'])

        # 3. Close the Main Case
        case = trial.case
        case.status = case.STATUS_CLOSED
        case.save(update_fields=['status'])

        # 4. Log the action
        log_audit(self.request.user, 'create', 'Verdict', verdict.pk, verdict.title)



















# """
# Trial and verdict. Judge views full case and records verdict + punishment.
# """
# from rest_framework import generics, status
# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework.permissions import IsAuthenticated

# from django.shortcuts import get_object_or_404

# from .models import Trial, Verdict
# from .serializers import TrialSerializer, VerdictSerializer, VerdictCreateSerializer
# from accounts.permissions import IsJudge, CanReferCaseToJudiciary
# from core.utils import log_audit


# class TrialListCreateView(generics.ListCreateAPIView):
#     """List trials; create trial when case referred to judiciary (Captain/Chief/Judge)."""
#     permission_classes = [IsAuthenticated]
#     serializer_class = TrialSerializer
#     queryset = Trial.objects.all().order_by('-started_at')

#     def get_permissions(self):
#         if self.request.method == 'GET':
#             return [IsAuthenticated(), IsJudge()]
#         return [IsAuthenticated(), CanReferCaseToJudiciary()]

#     def perform_create(self, serializer):
#         judge = self.request.user if self.request.user.has_role('Judge') else None
#         trial = serializer.save(judge=judge)
#         trial.case.status = trial.case.STATUS_REFERRED_TO_JUDICIARY
#         trial.case.save(update_fields=['status'])


# class TrialDetailView(generics.RetrieveUpdateAPIView):
#     """Judge views full case history, reports, approvals, officers, evidence (via case detail)."""
#     permission_classes = [IsAuthenticated, IsJudge]
#     queryset = Trial.objects.all()
#     serializer_class = TrialSerializer


# class VerdictListCreateView(generics.ListCreateAPIView):
#     """List verdicts; judge records verdict + punishment."""
#     permission_classes = [IsAuthenticated, IsJudge]
#     serializer_class = VerdictSerializer

#     def get_queryset(self):
#         return Verdict.objects.all().order_by('-recorded_at')

#     def get_serializer_class(self):
#         if self.request.method == 'POST':
#             return VerdictCreateSerializer
#         return VerdictSerializer

#     def perform_create(self, serializer):
#         verdict = serializer.save(recorded_by=self.request.user)
#         log_audit(self.request.user, 'create', 'Verdict', verdict.pk, verdict.title)
