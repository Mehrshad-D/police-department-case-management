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
