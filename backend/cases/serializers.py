"""
Case, Complaint, CrimeScene, CaseComplainant serializers.
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Case, Complaint, CaseComplainant, CrimeSceneReport

User = get_user_model()


class CaseListSerializer(serializers.ModelSerializer):
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    assigned_detective_username = serializers.CharField(
        source='assigned_detective.username', read_only=True, allow_null=True
    )

    class Meta:
        model = Case
        fields = [
            'id', 'title', 'description', 'severity', 'status', 'is_crime_scene_case',
            'created_by', 'created_by_username', 'assigned_detective', 'assigned_detective_username',
            'approved_by_captain', 'created_at', 'updated_at',
        ]


class CaseDetailSerializer(serializers.ModelSerializer):
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    complainants = serializers.SerializerMethodField()
    complaint_origin = serializers.SerializerMethodField()

    class Meta:
        model = Case
        fields = [
            'id', 'title', 'description', 'severity', 'status', 'is_crime_scene_case',
            'created_by', 'created_by_username', 'assigned_detective', 'approved_by_captain',
            'complainants', 'complaint_origin', 'created_at', 'updated_at',
        ]

    def get_complainants(self, obj):
        return CaseComplainantSerializer(obj.complainants.all(), many=True).data

    def get_complaint_origin(self, obj):
        if hasattr(obj, 'complaint_origin') and obj.complaint_origin:
            return ComplaintListSerializer(obj.complaint_origin).data
        return None


class CaseCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Case
        fields = [
            'title', 'description', 'severity', 'status', 'is_crime_scene_case',
            'assigned_detective',
        ]


class ComplaintListSerializer(serializers.ModelSerializer):
    complainant_username = serializers.CharField(source='complainant.username', read_only=True)

    class Meta:
        model = Complaint
        fields = [
            'id', 'complainant', 'complainant_username', 'title', 'description',
            'status', 'correction_count', 'last_correction_message', 'case',
            'created_at', 'updated_at',
        ]


class ComplaintDetailSerializer(serializers.ModelSerializer):
    complainant_username = serializers.CharField(source='complainant.username', read_only=True)

    class Meta:
        model = Complaint
        fields = [
            'id', 'complainant', 'complainant_username', 'title', 'description',
            'status', 'correction_count', 'last_correction_message',
            'reviewed_by_trainee', 'reviewed_by_officer', 'case',
            'created_at', 'updated_at',
        ]


class ComplaintCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Complaint
        fields = ['title', 'description']

    def create(self, validated_data):
        validated_data['complainant'] = self.context['request'].user
        validated_data['status'] = Complaint.STATUS_PENDING_TRAINEE
        return super().create(validated_data)


class ComplaintCorrectSerializer(serializers.Serializer):
    """Complainant resubmits after correction."""
    title = serializers.CharField(required=False)
    description = serializers.CharField(required=False)


class ComplaintTraineeReviewSerializer(serializers.Serializer):
    """Trainee: approve (forward to officer) or return for correction."""
    action = serializers.ChoiceField(choices=['approve', 'return_correction'])
    correction_message = serializers.CharField(required=False, allow_blank=True)

    def validate(self, data):
        if data['action'] == 'return_correction' and not data.get('correction_message'):
            raise serializers.ValidationError('correction_message required when returning for correction')
        return data


class ComplaintOfficerReviewSerializer(serializers.Serializer):
    """Officer: approve (create case) or send back to trainee."""
    action = serializers.ChoiceField(choices=['approve', 'send_back'])


class CaseComplainantSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = CaseComplainant
        fields = ['id', 'case', 'user', 'user_username', 'is_primary', 'notes', 'added_at']


class CaseComplainantCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CaseComplainant
        fields = ['user', 'is_primary', 'notes']


class CrimeSceneReportSerializer(serializers.ModelSerializer):
    reported_by_username = serializers.CharField(source='reported_by.username', read_only=True)

    class Meta:
        model = CrimeSceneReport
        fields = [
            'id', 'case', 'reported_by', 'reported_by_username', 'scene_datetime',
            'location_description', 'witnesses_contact_info',
            'approved_by_supervisor', 'approved_at', 'created_at', 'updated_at',
        ]
        read_only_fields = ['approved_at']


class CrimeSceneReportCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CrimeSceneReport
        fields = ['case', 'scene_datetime', 'location_description', 'witnesses_contact_info']


class CrimeSceneReportApproveSerializer(serializers.Serializer):
    """Supervisor approves crime scene report (or chief creates without approval)."""
    approved = serializers.BooleanField()
