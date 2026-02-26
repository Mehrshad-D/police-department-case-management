"""
Evidence serializers: base + witness (transcript, media), biological (images, verification), vehicle, ID doc, other.
Validation: file types/sizes, vehicle constraint, biological >=1 image.
"""
from rest_framework import serializers
from django.core.files.uploadedfile import UploadedFile

from cases.models import Case
from .models import (
    Evidence,
    WitnessEvidence,
    WitnessMedia,
    BiologicalEvidence,
    BiologicalEvidenceImage,
    VehicleEvidence,
    IDDocumentEvidence,
    EvidenceLink,
    EVIDENCE_FILE_MAX_SIZE,
    ALLOWED_IMAGE_TYPES,
    ALLOWED_VIDEO_TYPES,
    ALLOWED_AUDIO_TYPES,
)


def validate_file_size(file: UploadedFile, max_size: int = EVIDENCE_FILE_MAX_SIZE):
    if file.size > max_size:
        raise serializers.ValidationError(
            f'File size must not exceed {max_size // (1024 * 1024)} MB.'
        )


def validate_witness_media_type(file: UploadedFile, media_type: str):
    content_type = getattr(file, 'content_type', '') or ''
    if media_type == 'image' and content_type not in ALLOWED_IMAGE_TYPES:
        raise serializers.ValidationError(
            f'Image type not allowed. Allowed: {", ".join(ALLOWED_IMAGE_TYPES)}'
        )
    if media_type == 'video' and content_type not in ALLOWED_VIDEO_TYPES:
        raise serializers.ValidationError(
            f'Video type not allowed. Allowed: {", ".join(ALLOWED_VIDEO_TYPES)}'
        )
    if media_type == 'audio' and content_type not in ALLOWED_AUDIO_TYPES:
        raise serializers.ValidationError(
            f'Audio type not allowed. Allowed: {", ".join(ALLOWED_AUDIO_TYPES)}'
        )


class EvidenceListSerializer(serializers.ModelSerializer):
    recorder_username = serializers.CharField(source='recorder.username', read_only=True)
    date_recorded = serializers.DateTimeField(source='created_at', read_only=True)

    class Meta:
        model = Evidence
        fields = [
            'id', 'case', 'evidence_type', 'title', 'description',
            'date_recorded', 'recorder', 'recorder_username', 'created_at', 'updated_at',
        ]


class WitnessMediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = WitnessMedia
        fields = ['id', 'file', 'media_type', 'uploaded_at']


class WitnessEvidenceSerializer(serializers.ModelSerializer):
    media_files = WitnessMediaSerializer(many=True, read_only=True)

    class Meta:
        model = WitnessEvidence
        fields = ['transcript', 'statement', 'media_file', 'media_url', 'media_files']


class BiologicalEvidenceImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = BiologicalEvidenceImage
        fields = ['id', 'image', 'caption', 'uploaded_at']


class BiologicalEvidenceSerializer(serializers.ModelSerializer):
    images = BiologicalEvidenceImageSerializer(many=True, read_only=True)

    class Meta:
        model = BiologicalEvidence
        fields = [
            'verification_status', 'verification_result',
            'reviewed_by', 'reviewed_at', 'images',
        ]


class VehicleEvidenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = VehicleEvidence
        fields = ['model', 'color', 'license_plate', 'serial_number']

    def validate(self, data):
        plate = (data.get('license_plate') or '').strip()
        serial = (data.get('serial_number') or '').strip()
        if plate and serial:
            raise serializers.ValidationError(
                'Provide exactly one of license_plate or serial_number, not both.'
            )
        if not plate and not serial:
            raise serializers.ValidationError(
                'Provide exactly one of license_plate or serial_number.'
            )
        return data


class IDDocumentEvidenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = IDDocumentEvidence
        fields = ['owner_full_name', 'attributes']


class EvidenceDetailSerializer(serializers.ModelSerializer):
    recorder_username = serializers.CharField(source='recorder.username', read_only=True)
    date_recorded = serializers.DateTimeField(source='created_at', read_only=True)
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
    """Create evidence with type-specific payload. Validates file types/sizes and constraints."""
    case = serializers.PrimaryKeyRelatedField(queryset=Case.objects.all())
    evidence_type = serializers.ChoiceField(choices=Evidence.TYPE_CHOICES)
    title = serializers.CharField(max_length=255)
    description = serializers.CharField(required=False, allow_blank=True, default='')

    # Witness
    transcript = serializers.CharField(required=False, allow_blank=True, default='')
    media_file = serializers.FileField(required=False, allow_null=True)
    media_url = serializers.URLField(required=False, allow_blank=True)
    media_files = serializers.ListField(
        child=serializers.DictField(child=serializers.CharField()),
        required=False,
        default=list,
    )  # [{"file": <upload>, "media_type": "image"|"video"|"audio"}]

    # Biological: images required (>=1) — passed via request.FILES.getlist('images')
    images = serializers.ListField(
        child=serializers.ImageField(allow_empty_file=False),
        required=False,
        default=list,
    )

    # Vehicle: exactly one of license_plate or serial_number
    model = serializers.CharField(required=False, allow_blank=True, default='')
    color = serializers.CharField(required=False, allow_blank=True, default='')
    license_plate = serializers.CharField(required=False, allow_blank=True, default='')
    serial_number = serializers.CharField(required=False, allow_blank=True, default='')

    # ID Document
    owner_full_name = serializers.CharField(required=False, allow_blank=True, default='')
    attributes = serializers.JSONField(required=False, default=dict)

    def validate_evidence_type(self, value):
        return value

    def validate(self, data):
        request = self.context.get('request')
        if request and request.FILES:
            # Multipart: multiple images under key 'images'
            data = dict(data)
            data['images'] = request.FILES.getlist('images') or data.get('images') or []
            # Witness media_files: list of {file, media_type} from request
            if data.get('evidence_type') == Evidence.TYPE_WITNESS:
                media_files = []
                for i in range(100):
                    f = request.FILES.get(f'media_files_{i}')
                    mt = request.data.get(f'media_files_{i}_type', 'image')
                    if f:
                        media_files.append({'file': f, 'media_type': mt})
                if media_files:
                    data['media_files'] = media_files
        evidence_type = data['evidence_type']
        if evidence_type == Evidence.TYPE_BIOLOGICAL:
            images = data.get('images') or []
            if not images:
                raise serializers.ValidationError(
                    {'images': 'At least one image is required for biological evidence.'}
                )
            for img in images:
                validate_file_size(img)
        if evidence_type == Evidence.TYPE_VEHICLE:
            plate = (data.get('license_plate') or '').strip()
            serial = (data.get('serial_number') or '').strip()
            if plate and serial:
                raise serializers.ValidationError(
                    'Provide exactly one of license_plate or serial_number, not both.'
                )
            if not plate and not serial:
                raise serializers.ValidationError(
                    'Provide exactly one of license_plate or serial_number.'
                )
        if evidence_type == Evidence.TYPE_WITNESS:
            if data.get('media_file'):
                validate_file_size(data['media_file'])
            for item in data.get('media_files') or []:
                f = item.get('file')
                if f:
                    validate_file_size(f)
                    validate_witness_media_type(f, item.get('media_type') or 'image')
        return data

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
            we = WitnessEvidence.objects.create(
                evidence=evidence,
                transcript=validated_data.get('transcript', ''),
                statement='',
                media_file=validated_data.get('media_file'),
                media_url=validated_data.get('media_url', ''),
            )
            for item in validated_data.get('media_files') or []:
                f = item.get('file')
                mt = item.get('media_type') or 'image'
                if f:
                    WitnessMedia.objects.create(witness_evidence=we, file=f, media_type=mt)

        elif evidence_type == Evidence.TYPE_BIOLOGICAL:
            bio = BiologicalEvidence.objects.create(evidence=evidence)
            for img in validated_data.get('images') or []:
                BiologicalEvidenceImage.objects.create(biological_evidence=bio, image=img)

        elif evidence_type == Evidence.TYPE_VEHICLE:
            VehicleEvidence.objects.create(
                evidence=evidence,
                model=validated_data.get('model', ''),
                color=validated_data.get('color', ''),
                license_plate=validated_data.get('license_plate', ''),
                serial_number=validated_data.get('serial_number', ''),
            )

        elif evidence_type == Evidence.TYPE_ID_DOCUMENT:
            IDDocumentEvidence.objects.create(
                evidence=evidence,
                owner_full_name=validated_data.get('owner_full_name', ''),
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
