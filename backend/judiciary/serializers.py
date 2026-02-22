from rest_framework import serializers
from .models import Trial, Verdict


class TrialSerializer(serializers.ModelSerializer):
    judge_username = serializers.CharField(source='judge.username', read_only=True, allow_null=True)
    case_title = serializers.CharField(source='case.title', read_only=True)

    class Meta:
        model = Trial
        fields = ['id', 'case', 'case_title', 'judge', 'judge_username', 'started_at', 'closed_at']
        read_only_fields = ['started_at']
        extra_kwargs = {'closed_at': {'required': False}}


class FullTrialDetailSerializer(TrialSerializer):
    """Used for TrialDetailView to provide the Judge with comprehensive case context."""
    case_context = serializers.SerializerMethodField()

    class Meta(TrialSerializer.Meta):
        fields = TrialSerializer.Meta.fields + ['case_context']

    def get_case_context(self, obj):
        case = obj.case
        return {
            "severity": case.get_severity_display(),
            "status": case.get_status_display(),
            "is_crime_scene_case": case.is_crime_scene_case,
            "officers": {
                "created_by": case.created_by.username if case.created_by else None,
                "assigned_detective": case.assigned_detective.username if case.assigned_detective else None,
                "approved_by_captain": case.approved_by_captain.username if case.approved_by_captain else None,
            },
            "complainants_count": case.complainants.count() if hasattr(case, 'complainants') else 0,
            "has_crime_scene_report": hasattr(case, 'crime_scene_report'),
            # Frontend can use standard case/evidence endpoints for detailed arrays based on case_id
        }


class VerdictSerializer(serializers.ModelSerializer):
    class Meta:
        model = Verdict
        fields = [
            'id', 'trial', 'title', 'description',
            'punishment_title', 'punishment_description',
            'recorded_at', 'recorded_by',
        ]


class VerdictCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Verdict
        fields = ['trial', 'title', 'description', 'punishment_title', 'punishment_description']



















# from rest_framework import serializers
# from .models import Trial, Verdict


# class TrialSerializer(serializers.ModelSerializer):
#     judge_username = serializers.CharField(source='judge.username', read_only=True, allow_null=True)
#     case_title = serializers.CharField(source='case.title', read_only=True)

#     class Meta:
#         model = Trial
#         fields = ['id', 'case', 'case_title', 'judge', 'judge_username', 'started_at', 'closed_at']
#         read_only_fields = ['started_at']
#         extra_kwargs = {'closed_at': {'required': False}}


# class VerdictSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Verdict
#         fields = [
#             'id', 'trial', 'title', 'description',
#             'punishment_title', 'punishment_description',
#             'recorded_at', 'recorded_by',
#         ]


# class VerdictCreateSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Verdict
#         fields = ['trial', 'title', 'description', 'punishment_title', 'punishment_description']
