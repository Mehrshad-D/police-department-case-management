"""
Evidence CRUD, biological evidence review (forensic doctor), evidence linking.
"""
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from django.shortcuts import get_object_or_404
from django.utils import timezone

from .models import Evidence, BiologicalEvidence, BiologicalEvidenceImage, EvidenceLink
from .serializers import (
    EvidenceListSerializer,
    EvidenceDetailSerializer,
    EvidenceCreateSerializer,
    EvidenceLinkSerializer,
    EvidenceLinkCreateSerializer,
    BiologicalEvidenceImageSerializer,
)
from accounts.permissions import IsOfficerOrAbove, IsForensicDoctor
from core.utils import log_audit, notify


class EvidenceListCreateView(generics.ListCreateAPIView):
    """List evidence (filter by case); create evidence (officer/detective)."""
    permission_classes = [IsAuthenticated, IsOfficerOrAbove]
    serializer_class = EvidenceListSerializer

    def get_queryset(self):
        qs = Evidence.objects.all()
        case_id = self.request.query_params.get('case')
        if case_id:
            qs = qs.filter(case_id=case_id)
        return qs.order_by('-created_at')

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return EvidenceCreateSerializer
        return EvidenceListSerializer

    def perform_create(self, serializer):
        evidence = serializer.save()
        log_audit(self.request.user, 'create', 'Evidence', evidence.pk, f'Evidence added: {evidence.title}')
        if evidence.case.assigned_detective_id:
            notify(
                evidence.case.assigned_detective,
                'New evidence added',
                f'Case #{evidence.case_id}: {evidence.title}',
                'evidence_added',
                'Evidence',
                evidence.pk,
            )


class EvidenceDetailView(generics.RetrieveDestroyAPIView):
    permission_classes = [IsAuthenticated, IsOfficerOrAbove]
    queryset = Evidence.objects.all()
    serializer_class = EvidenceDetailSerializer


class BiologicalEvidenceReviewView(APIView):
    """Forensic doctor approves or rejects biological evidence validity."""
    permission_classes = [IsAuthenticated, IsForensicDoctor]

    def post(self, request, pk):
        evidence = get_object_or_404(Evidence, pk=pk, evidence_type=Evidence.TYPE_BIOLOGICAL)
        if not hasattr(evidence, 'biological_detail'):
            return Response(
                {'success': False, 'error': {'message': 'Not biological evidence.'}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        bio = evidence.biological_detail
        status_val = request.data.get('verification_status')
        allowed = (BiologicalEvidence.STATUS_VERIFIED_FORENSIC, BiologicalEvidence.STATUS_VERIFIED_NATIONAL_DB, BiologicalEvidence.STATUS_REJECTED)
        if status_val not in allowed:
            return Response(
                {'success': False, 'error': {'message': 'verification_status must be verified_forensic, verified_national_db, or rejected.'}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        bio.verification_status = status_val
        bio.verification_result = request.data.get('verification_result') or ''
        bio.reviewed_by = request.user
        bio.reviewed_at = timezone.now()
        bio.save()
        log_audit(request.user, 'update', 'BiologicalEvidence', bio.pk, f'Verification {status_val}')
        if evidence.case.assigned_detective_id:
            notify(
                evidence.case.assigned_detective,
                f'Biological evidence {status_val}',
                evidence.title,
                'biological_evidence_reviewed',
                'Evidence',
                evidence.pk,
            )
        return Response({'success': True, 'data': EvidenceDetailSerializer(evidence).data})


class BiologicalEvidenceAddImageView(APIView):
    """Add image to biological evidence."""
    permission_classes = [IsAuthenticated, IsOfficerOrAbove]

    def post(self, request, pk):
        evidence = get_object_or_404(Evidence, pk=pk, evidence_type=Evidence.TYPE_BIOLOGICAL)
        bio = get_object_or_404(BiologicalEvidence, evidence=evidence)
        ser = BiologicalEvidenceImageSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        ser.save(biological_evidence=bio)
        return Response(ser.data, status=status.HTTP_201_CREATED)


class EvidenceLinkListCreateView(generics.ListCreateAPIView):
    """List/create evidence links for a case (detective visual board)."""
    permission_classes = [IsAuthenticated, IsOfficerOrAbove]
    serializer_class = EvidenceLinkSerializer

    def get_queryset(self):
        return EvidenceLink.objects.filter(case_id=self.kwargs['case_pk'])

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return EvidenceLinkCreateSerializer
        return EvidenceLinkSerializer

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx['case_id'] = self.kwargs['case_pk']
        return ctx

    def perform_create(self, serializer):
        serializer.save()


class EvidenceLinkDetailView(generics.RetrieveDestroyAPIView):
    """Retrieve or delete a single evidence link."""
    permission_classes = [IsAuthenticated, IsOfficerOrAbove]
    serializer_class = EvidenceLinkSerializer

    def get_queryset(self):
        return EvidenceLink.objects.filter(case_id=self.kwargs['case_pk'])
