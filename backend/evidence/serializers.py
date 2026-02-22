"""
Evidence serializers: base + witness, biological, vehicle, ID document, other.
"""
from rest_framework import serializers
from cases.models import Case
from .models import (
    Evidence,
    WitnessEvidence,
    BiologicalEvidence,
    BiologicalEvidenceImage,
    VehicleEvidence,
    IDDocumentEvidence,
    EvidenceLink,
)


class EvidenceListSerializer(serializers.ModelSerializer):
    recorder_username = serializers.CharField(source='recorder.username', read_only=True)

    class Meta:
        model = Evidence
        fields = [
            'id', 'case', 'evidence_type', 'title', 'description',
            'date_recorded', 'recorder', 'recorder_username', 'created_at', 'updated_at',
        ]


class WitnessEvidenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = WitnessEvidence
        fields = ['statement', 'media_file', 'media_url']


class BiologicalEvidenceImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = BiologicalEvidenceImage
        fields = ['id', 'image', 'caption', 'uploaded_at']


class BiologicalEvidenceSerializer(serializers.ModelSerializer):
    images = BiologicalEvidenceImageSerializer(many=True, read_only=True)

    class Meta:
        model = BiologicalEvidence
        fields = ['lab_results', 'validity_status', 'reviewed_by', 'reviewed_at', 'images']


class VehicleEvidenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = VehicleEvidence
        fields = ['plate_number', 'serial_number', 'make_model']

    def validate(self, data):
        plate = data.get('plate_number', '')
        serial = data.get('serial_number', '')
        if plate and serial:
            raise serializers.ValidationError('Provide either plate_number or serial_number, not both.')
        if not plate and not serial:
            raise serializers.ValidationError('Provide either plate_number or serial_number.')
        return data


class IDDocumentEvidenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = IDDocumentEvidence
        fields = ['attributes']


class EvidenceDetailSerializer(serializers.ModelSerializer):
    recorder_username = serializers.CharField(source='recorder.username', read_only=True)
    witness_detail = WitnessEvidenceSerializer(read_only=True, allow_null=True)
    biological_detail = BiologicalEvidenceSerializer(read_only=True, allow_null=True)
    vehicle_detail = VehicleEvidenceSerializer(read_only=True, allow_null=True)
    id_document_detail = IDDocumentEvidenceSerializer(read_only=True, allow_null=True)

    class Meta:
        model = Evidence
        fields = [
            'id', 'case', 'evidence_type', 'title', 'description',
            'date_recorded', 'recorder', 'recorder_username',
            'witness_detail', 'biological_detail', 'vehicle_detail', 'id_document_detail',
            'created_at', 'updated_at',
        ]


class EvidenceCreateSerializer(serializers.Serializer):
    """Create evidence with type-specific payload."""
    case = serializers.PrimaryKeyRelatedField(queryset=Case.objects.all())
    evidence_type = serializers.ChoiceField(choices=Evidence.TYPE_CHOICES)
    title = serializers.CharField()
    description = serializers.CharField(required=False, allow_blank=True)
    # Type-specific
    statement = serializers.CharField(required=False, allow_blank=True)
    media_file = serializers.FileField(required=False, allow_null=True)
    media_url = serializers.URLField(required=False, allow_blank=True)
    lab_results = serializers.CharField(required=False, allow_blank=True)
    plate_number = serializers.CharField(required=False, allow_blank=True)
    serial_number = serializers.CharField(required=False, allow_blank=True)
    make_model = serializers.CharField(required=False, allow_blank=True)
    attributes = serializers.JSONField(required=False)

    def validate_evidence_type(self, value):
        if value == Evidence.TYPE_VEHICLE:
            plate = self.initial_data.get('plate_number', '')
            serial = self.initial_data.get('serial_number', '')
            if plate and serial:
                raise serializers.ValidationError('Provide either plate_number or serial_number, not both.')
            if not plate and not serial:
                raise serializers.ValidationError('Provide either plate_number or serial_number.')
        return value

    def create(self, validated_data):
        case = validated_data['case']
        evidence_type = validated_data['evidence_type']
        title = validated_data['title']
        description = validated_data.get('description', '')
        recorder = self.context['request'].user
        evidence = Evidence.objects.create(
            case=case,
            evidence_type=evidence_type,
            title=title,
            description=description,
            recorder=recorder,
        )
        if evidence_type == Evidence.TYPE_WITNESS:
            WitnessEvidence.objects.create(
                evidence=evidence,
                statement=validated_data.get('statement', ''),
                media_file=validated_data.get('media_file'),
                media_url=validated_data.get('media_url', ''),
            )
        elif evidence_type == Evidence.TYPE_BIOLOGICAL:
            BiologicalEvidence.objects.create(
                evidence=evidence,
                lab_results=validated_data.get('lab_results', ''),
            )
        elif evidence_type == Evidence.TYPE_VEHICLE:
            VehicleEvidence.objects.create(
                evidence=evidence,
                plate_number=validated_data.get('plate_number', ''),
                serial_number=validated_data.get('serial_number', ''),
                make_model=validated_data.get('make_model', ''),
            )
        elif evidence_type == Evidence.TYPE_ID_DOCUMENT:
            IDDocumentEvidence.objects.create(
                evidence=evidence,
                attributes=validated_data.get('attributes', {}),
            )
        return evidence


class EvidenceLinkSerializer(serializers.ModelSerializer):
    evidence_from_title = serializers.CharField(source='evidence_from.title', read_only=True)
    evidence_to_title = serializers.CharField(source='evidence_to.title', read_only=True)

    class Meta:
        model = EvidenceLink
        fields = [
            'id', 'case', 'evidence_from', 'evidence_from_title', 'evidence_to', 'evidence_to_title',
            'link_type', 'created_by', 'created_at',
        ]


class EvidenceLinkCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = EvidenceLink
        fields = ['evidence_from', 'evidence_to', 'link_type']

    def create(self, validated_data):
        validated_data['case_id'] = self.context['case_id']
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)
