"""
Suspect, Interrogation, ArrestOrder serializers. Ranking and reward calculation.
"""
from rest_framework import serializers
from .models import Suspect, Interrogation, ArrestOrder


class SuspectListSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source='user.username', read_only=True)
    case_title = serializers.CharField(source='case.title', read_only=True)
    days_pursued = serializers.ReadOnlyField()
    ranking_score = serializers.SerializerMethodField()
    reward_rials = serializers.SerializerMethodField()

    class Meta:
        model = Suspect
        fields = [
            'id', 'case', 'case_title', 'user', 'user_username', 'status',
            'proposed_by_detective', 'approved_by_supervisor', 'approved_at',
            'marked_at', 'first_pursuit_date', 'days_pursued',
            'ranking_score', 'reward_rials',
        ]

    def get_ranking_score(self, obj):
        # Ranking score = days_pursued × crime severity weight (higher = more severe: crisis=4, level1=3, etc.)
        days = obj.days_pursued
        severity_weight = 4 - obj.case.severity  # 3->1, 2->2, 1->3, 0(crisis)->4
        return days * severity_weight

    def get_reward_rials(self, obj):
        score = self.get_ranking_score(obj)
        return score * 20_000_000


class SuspectDetailSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source='user.username', read_only=True)
    case_title = serializers.CharField(source='case.title', read_only=True)
    interrogations = serializers.SerializerMethodField()

    class Meta:
        model = Suspect
        fields = [
            'id', 'case', 'case_title', 'user', 'user_username', 'status',
            'proposed_by_detective', 'approved_by_supervisor', 'approved_at',
            'marked_at', 'first_pursuit_date', 'interrogations',
        ]

    def get_interrogations(self, obj):
        return InterrogationSerializer(obj.interrogations.all(), many=True).data


class SuspectProposeSerializer(serializers.Serializer):
    """Detective proposes a suspect (user_id, case_id)."""
    user_id = serializers.IntegerField()
    case_id = serializers.IntegerField()


class SuspectSupervisorReviewSerializer(serializers.Serializer):
    """Supervisor approves (arrest starts) or rejects."""
    action = serializers.ChoiceField(choices=['approve', 'reject'])


class InterrogationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Interrogation
        fields = [
            'id', 'suspect', 'detective_probability', 'supervisor_probability',
            'captain_decision', 'captain_decided_by', 'captain_decided_at',
            'chief_confirmed', 'chief_confirmed_at', 'created_at', 'updated_at',
        ]


class InterrogationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Interrogation
        fields = ['suspect', 'detective_probability', 'supervisor_probability']


class InterrogationCaptainDecisionSerializer(serializers.Serializer):
    captain_decision = serializers.CharField()


class ArrestOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = ArrestOrder
        fields = ['id', 'suspect', 'issued_by', 'order_type', 'notes', 'issued_at']
