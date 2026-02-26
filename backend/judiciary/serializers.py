from rest_framework import serializers
from .models import Trial, Verdict
from cases.models import Case, CrimeSceneReport, CaseComplainant
from cases.serializers import CaseDetailSerializer, CrimeSceneReportSerializer, CaseComplainantSerializer
from evidence.serializers import EvidenceListSerializer
from suspects.serializers import SuspectListSerializer, InterrogationSerializer, CaptainDecisionSerializer, ChiefApprovalSerializer
from suspects.models import ChiefApproval


class TrialSerializer(serializers.ModelSerializer):
    judge_username = serializers.CharField(source='judge.username', read_only=True, allow_null=True)
    case_title = serializers.CharField(source='case.title', read_only=True)

    class Meta:
        model = Trial
        fields = ['id', 'case', 'case_title', 'judge', 'judge_username', 'started_at', 'closed_at']
        read_only_fields = ['started_at']
        extra_kwargs = {'closed_at': {'required': False}}


class VerdictSerializer(serializers.ModelSerializer):
    class Meta:
        model = Verdict
        fields = [
            'id', 'trial', 'verdict_type', 'title', 'description',
            'punishment_title', 'punishment_description',
            'recorded_at', 'recorded_by',
        ]


class VerdictCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Verdict
        fields = ['trial', 'verdict_type', 'title', 'description', 'punishment_title', 'punishment_description']


class TrialFullDetailSerializer(serializers.ModelSerializer):
    """Full case data for Judge: case, evidence, reports, approvals, all personnel."""
    judge_username = serializers.CharField(source='judge.username', read_only=True, allow_null=True)
    case_data = serializers.SerializerMethodField()
    evidence_items = serializers.SerializerMethodField()
    crime_scene_report = serializers.SerializerMethodField()
    complainants = serializers.SerializerMethodField()
    suspects = serializers.SerializerMethodField()
    personnel = serializers.SerializerMethodField()

    class Meta:
        model = Trial
        fields = [
            'id', 'case', 'judge', 'judge_username', 'started_at', 'closed_at',
            'case_data', 'evidence_items', 'crime_scene_report', 'complainants',
            'suspects', 'personnel',
        ]

    def get_case_data(self, obj):
        return CaseDetailSerializer(obj.case).data

    def get_evidence_items(self, obj):
        from evidence.models import Evidence
        items = Evidence.objects.filter(case=obj.case).order_by('-created_at')
        return EvidenceListSerializer(items, many=True).data

    def get_crime_scene_report(self, obj):
        if getattr(obj.case, 'crime_scene_report', None):
            return CrimeSceneReportSerializer(obj.case.crime_scene_report).data
        return None

    def get_complainants(self, obj):
        return CaseComplainantSerializer(obj.case.complainants.all(), many=True).data

    def get_suspects(self, obj):
        return SuspectListSerializer(obj.case.suspects.all(), many=True).data

    def get_personnel(self, obj):
        """All police personnel involved: created_by, assigned_detective, approved_by_captain, etc."""
        case = obj.case
        users = set()
        if case.created_by_id:
            users.add(case.created_by_id)
        if case.assigned_detective_id:
            users.add(case.assigned_detective_id)
        if case.approved_by_captain_id:
            users.add(case.approved_by_captain_id)
        if getattr(case, 'crime_scene_report', None) and case.crime_scene_report.reported_by_id:
            users.add(case.crime_scene_report.reported_by_id)
        if getattr(case, 'crime_scene_report', None) and case.crime_scene_report.approved_by_supervisor_id:
            users.add(case.crime_scene_report.approved_by_supervisor_id)
        for s in case.suspects.all():
            if s.proposed_by_detective_id:
                users.add(s.proposed_by_detective_id)
            if s.approved_by_supervisor_id:
                users.add(s.approved_by_supervisor_id)
        for cd in case.captain_decisions.all():
            if cd.decided_by_id:
                users.add(cd.decided_by_id)
        from django.contrib.auth import get_user_model
        User = get_user_model()
        return [
            {'id': u.id, 'username': u.username, 'full_name': u.full_name, 'role_names': u.role_names()}
            for u in User.objects.filter(pk__in=users)
        ]


class TrialFullDataByCaseSerializer(serializers.Serializer):
    """Full case data for judge by case_id: case, evidence, interrogations, captain decisions, chief approvals, personnel."""
    case_data = serializers.SerializerMethodField()
    evidence_items = serializers.SerializerMethodField()
    crime_scene_report = serializers.SerializerMethodField()
    complainants = serializers.SerializerMethodField()
    suspects = serializers.SerializerMethodField()
    interrogations = serializers.SerializerMethodField()
    captain_decisions = serializers.SerializerMethodField()
    chief_approvals = serializers.SerializerMethodField()
    personnel = serializers.SerializerMethodField()
    trial = serializers.SerializerMethodField()
    verdict = serializers.SerializerMethodField()

    def _case(self):
        return self.instance

    def get_case_data(self, obj):
        return CaseDetailSerializer(self._case()).data

    def get_evidence_items(self, obj):
        from evidence.models import Evidence
        items = Evidence.objects.filter(case=self._case()).order_by('-created_at')
        return EvidenceListSerializer(items, many=True).data

    def get_crime_scene_report(self, obj):
        case = self._case()
        if getattr(case, 'crime_scene_report', None):
            return CrimeSceneReportSerializer(case.crime_scene_report).data
        return None

    def get_complainants(self, obj):
        return CaseComplainantSerializer(self._case().complainants.all(), many=True).data

    def get_suspects(self, obj):
        return SuspectListSerializer(self._case().suspects.all(), many=True).data

    def get_interrogations(self, obj):
        from suspects.models import Interrogation
        qs = Interrogation.objects.filter(suspect__case=self._case()).select_related('suspect').order_by('-created_at')
        return InterrogationSerializer(qs, many=True).data

    def get_captain_decisions(self, obj):
        return CaptainDecisionSerializer(self._case().captain_decisions.all(), many=True).data

    def get_chief_approvals(self, obj):
        approvals = ChiefApproval.objects.filter(captain_decision__case=self._case()).select_related('captain_decision')
        return ChiefApprovalSerializer(approvals, many=True).data

    def get_personnel(self, obj):
        case = self._case()
        users = set()
        if case.created_by_id:
            users.add(case.created_by_id)
        if case.assigned_detective_id:
            users.add(case.assigned_detective_id)
        if case.approved_by_captain_id:
            users.add(case.approved_by_captain_id)
        if getattr(case, 'crime_scene_report', None) and case.crime_scene_report.reported_by_id:
            users.add(case.crime_scene_report.reported_by_id)
        if getattr(case, 'crime_scene_report', None) and case.crime_scene_report.approved_by_supervisor_id:
            users.add(case.crime_scene_report.approved_by_supervisor_id)
        for s in case.suspects.all():
            if s.proposed_by_detective_id:
                users.add(s.proposed_by_detective_id)
            if s.approved_by_supervisor_id:
                users.add(s.approved_by_supervisor_id)
        for cd in case.captain_decisions.all():
            if cd.decided_by_id:
                users.add(cd.decided_by_id)
        from django.contrib.auth import get_user_model
        User = get_user_model()
        return [{'id': u.id, 'username': u.username, 'full_name': u.full_name, 'role_names': u.role_names()} for u in User.objects.filter(pk__in=users)]

    def get_trial(self, obj):
        case = self._case()
        if getattr(case, 'trial', None):
            return TrialSerializer(case.trial).data
        return None

    def get_verdict(self, obj):
        case = self._case()
        if getattr(case, 'trial', None) and getattr(case.trial, 'verdict', None):
            return VerdictSerializer(case.trial.verdict).data
        return None
