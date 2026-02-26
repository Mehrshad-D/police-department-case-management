"""
Suspect, Interrogation, ArrestOrder serializers. Ranking and reward calculation.
"""
from rest_framework import serializers
from .models import Suspect, Interrogation, ArrestOrder


class SuspectListSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source='user.username', read_only=True)
    user_full_name = serializers.CharField(source='user.full_name', read_only=True)
    user_national_id = serializers.CharField(source='user.national_id', read_only=True)
    case_title = serializers.CharField(source='case.title', read_only=True)
    days_pursued = serializers.SerializerMethodField()
    crime_degree = serializers.SerializerMethodField()
    ranking_score = serializers.SerializerMethodField()
    reward_rials = serializers.SerializerMethodField()

    class Meta:
        model = Suspect
        fields = [
            'id', 'case', 'case_title', 'user', 'user_username', 'user_full_name', 'user_national_id',
            'status', 'rejection_message',
            'proposed_by_detective', 'approved_by_supervisor', 'approved_at',
            'marked_at', 'first_pursuit_date', 'days_pursued', 'crime_degree',
            'ranking_score', 'reward_rials',
        ]

    def get_days_pursued(self, obj):
        return obj.days_under_investigation

    def get_crime_degree(self, obj):
        return obj.crime_degree() if hasattr(obj, 'crime_degree') else (4 - obj.case.severity)

    def get_ranking_score(self, obj):
        return obj.ranking_score() if hasattr(obj, 'ranking_score') else (getattr(obj, 'days_pursued', 0) or 0) * (4 - obj.case.severity)

    def get_reward_rials(self, obj):
        return obj.reward_rials() if hasattr(obj, 'reward_rials') else (getattr(obj, 'ranking_score', 0) or 0) * 20_000_000


class SuspectDetailSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source='user.username', read_only=True)
    user_full_name = serializers.CharField(source='user.full_name', read_only=True)
    case_title = serializers.CharField(source='case.title', read_only=True)
    interrogations = serializers.SerializerMethodField()

    class Meta:
        model = Suspect
        fields = [
            'id', 'case', 'case_title', 'user', 'user_username', 'user_full_name', 'status', 'rejection_message',
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
    """Sergeant approves (arrest starts) or rejects with message."""
    action = serializers.ChoiceField(choices=['approve', 'reject'])
    rejection_message = serializers.CharField(required=False, allow_blank=True)


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


class MostWantedPublicSerializer(serializers.ModelSerializer):
    """Public Most Wanted list: photo (placeholder), personal details, score, reward. Sorted by score."""
    user_full_name = serializers.CharField(source='user.full_name', read_only=True)
    user_username = serializers.CharField(source='user.username', read_only=True)
    case_title = serializers.CharField(source='case.title', read_only=True)
    days_under_investigation = serializers.SerializerMethodField()
    crime_degree = serializers.SerializerMethodField()
    ranking_score = serializers.SerializerMethodField()
    reward_rials = serializers.SerializerMethodField()
    photo = serializers.SerializerMethodField()

    class Meta:
        model = Suspect
        fields = [
            'id', 'user', 'user_username', 'user_full_name', 'photo',
            'case', 'case_title', 'days_under_investigation', 'crime_degree',
            'ranking_score', 'reward_rials', 'marked_at',
        ]

    def get_days_under_investigation(self, obj):
        return obj.days_under_investigation

    def get_crime_degree(self, obj):
        return obj.crime_degree()

    def get_ranking_score(self, obj):
        return obj.ranking_score()

    def get_reward_rials(self, obj):
        return obj.reward_rials()

    def get_photo(self, obj):
        return getattr(obj.user, 'photo', None) or None  # Optional User.photo; frontend can use placeholder
        

class ArrestOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = ArrestOrder
        fields = ['id', 'suspect', 'issued_by', 'order_type', 'notes', 'issued_at']
