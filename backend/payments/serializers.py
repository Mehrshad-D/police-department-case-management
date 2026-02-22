from rest_framework import serializers
from .models import BailPayment, FinePayment


class BailPaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = BailPayment
        fields = [
            'id', 'suspect', 'amount_rials', 'status',
            'approved_by_supervisor', 'approved_at', 'gateway_reference',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['status', 'approved_at']


class BailPaymentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = BailPayment
        fields = ['suspect', 'amount_rials']


class FinePaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = FinePayment
        fields = [
            'id', 'trial', 'payer', 'amount_rials', 'status',
            'gateway_reference', 'created_at', 'updated_at',
        ]
