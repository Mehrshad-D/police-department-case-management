from rest_framework import serializers
from .models import Tip, Reward


class TipListSerializer(serializers.ModelSerializer):
    submitter_username = serializers.CharField(source='submitter.username', read_only=True)

    class Meta:
        model = Tip
        fields = [
            'id', 'submitter', 'submitter_username', 'case', 'title', 'description',
            'status', 'reviewed_by_officer', 'reviewed_by_detective', 'created_at', 'updated_at',
        ]


class TipCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tip
        fields = ['case', 'title', 'description']

    def create(self, validated_data):
        validated_data['submitter'] = self.context['request'].user
        return super().create(validated_data)


class RewardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reward
        fields = [
            'id', 'tip', 'suspect', 'amount_rials', 'unique_code', 'recipient_national_id',
            'claimed', 'claimed_at', 'created_at',
        ]
        read_only_fields = ['unique_code']

class RewardClaimSerializer(serializers.Serializer):
    national_id = serializers.CharField()
    code = serializers.CharField()

class RewardClaimLookupSerializer(serializers.Serializer):
    """Police view reward info using national_id + code."""
    national_id = serializers.CharField()
    code = serializers.CharField()