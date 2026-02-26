"""
Trial and verdict. Judge views full case and records verdict + punishment.
"""
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from django.shortcuts import get_object_or_404

from .models import Trial, Verdict
from .serializers import (
    TrialSerializer,
    VerdictSerializer,
    VerdictCreateSerializer,
    TrialFullDetailSerializer,
    TrialFullDataByCaseSerializer,
)
from cases.models import Case
from accounts.permissions import IsJudge, CanReferCaseToJudiciary
from core.utils import log_audit


class TrialListCreateView(generics.ListCreateAPIView):
    """List trials; create trial when case referred to judiciary (Captain/Chief/Judge)."""
    permission_classes = [IsAuthenticated]
    serializer_class = TrialSerializer
    queryset = Trial.objects.all().order_by('-started_at')
    pagination_class = None  # Return full list so judge always sees all trials

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
    """Judge views trial; use trial-full-detail for full case data."""
    permission_classes = [IsAuthenticated]
    queryset = Trial.objects.all()
    serializer_class = TrialSerializer


class TrialFullDetailView(generics.RetrieveAPIView):
    """Judge: full case data, all evidence, all reports, all approvals, all police personnel."""
    permission_classes = [IsAuthenticated, IsJudge]
    queryset = Trial.objects.all()
    serializer_class = TrialFullDetailSerializer


class TrialFullDataByCaseView(APIView):
    """GET /api/trials/full-by-case/<case_id>/ — Judge: full case data by case_id (interrogations, captain decisions, chief approvals)."""
    permission_classes = [IsAuthenticated, IsJudge]

    def get(self, request, case_id):
        case = get_object_or_404(Case, pk=case_id)
        serializer = TrialFullDataByCaseSerializer(instance=case)
        return Response(serializer.data)


class VerdictListCreateView(generics.ListCreateAPIView):
    """List verdicts; judge records verdict + punishment."""
    permission_classes = [IsAuthenticated, IsJudge]
    serializer_class = VerdictSerializer

    def get_queryset(self):
        return Verdict.objects.all().order_by('-recorded_at')

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return VerdictCreateSerializer
        return VerdictSerializer

    def perform_create(self, serializer):
        verdict = serializer.save(recorded_by=self.request.user)
        log_audit(self.request.user, 'create', 'Verdict', verdict.pk, verdict.title or verdict.verdict_type)
        trial = verdict.trial
        from django.utils import timezone
        trial.closed_at = timezone.now()
        trial.save(update_fields=['closed_at'])
        if trial.suspect_id:
            from suspects.models import Suspect
            if verdict.verdict_type == Verdict.VERDICT_GUILTY:
                trial.suspect.mark_convicted()
            else:
                trial.suspect.mark_released()
