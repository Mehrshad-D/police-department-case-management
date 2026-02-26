"""
Evidence management: base evidence + types (witness, biological, vehicle, ID doc, other).
All evidence: title, description, created_at (auto), recorder (auto), case relation.
Uploads: validation, storage, media serving, size/type limits.
"""
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError


# Max file size for evidence uploads (10 MB)
EVIDENCE_FILE_MAX_SIZE = 10 * 1024 * 1024
ALLOWED_IMAGE_TYPES = ('image/jpeg', 'image/png', 'image/gif', 'image/webp')
ALLOWED_VIDEO_TYPES = ('video/mp4', 'video/webm', 'video/quicktime')
ALLOWED_AUDIO_TYPES = ('audio/mpeg', 'audio/wav', 'audio/ogg', 'audio/webm')


class Evidence(models.Model):
    """Base evidence: title, description, created_at, recorder, case. Subtypes add specific fields."""
    TYPE_WITNESS = 'witness'
    TYPE_BIOLOGICAL = 'biological'
    TYPE_VEHICLE = 'vehicle'
    TYPE_ID_DOCUMENT = 'id_document'
    TYPE_OTHER = 'other'
    TYPE_CHOICES = [
        (TYPE_WITNESS, 'Witness'),
        (TYPE_BIOLOGICAL, 'Biological'),
        (TYPE_VEHICLE, 'Vehicle'),
        (TYPE_ID_DOCUMENT, 'Identification Document'),
        (TYPE_OTHER, 'Other'),
    ]

    case = models.ForeignKey(
        'cases.Case',
        on_delete=models.CASCADE,
        related_name='evidence_items',
    )
    evidence_type = models.CharField(max_length=32, choices=TYPE_CHOICES)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    recorder = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='recorded_evidence',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['case', 'evidence_type']),
        ]
        verbose_name_plural = 'Evidence'

    def __str__(self):
        return f"{self.get_evidence_type_display()}: {self.title}"


class WitnessEvidence(models.Model):
    """Witness: transcript (optional), media files (image/video/audio)."""
    evidence = models.OneToOneField(
        Evidence,
        on_delete=models.CASCADE,
        related_name='witness_detail',
    )
    transcript = models.TextField(blank=True)
    # Legacy single file/URL for backward compatibility; prefer media_files
    statement = models.TextField(blank=True)
    media_file = models.FileField(upload_to='evidence/witness/', blank=True, null=True)
    media_url = models.URLField(blank=True)


class WitnessMedia(models.Model):
    """Witness evidence: multiple media files (image, video, audio)."""
    MEDIA_IMAGE = 'image'
    MEDIA_VIDEO = 'video'
    MEDIA_AUDIO = 'audio'
    MEDIA_CHOICES = [
        (MEDIA_IMAGE, 'Image'),
        (MEDIA_VIDEO, 'Video'),
        (MEDIA_AUDIO, 'Audio'),
    ]
    witness_evidence = models.ForeignKey(
        WitnessEvidence,
        on_delete=models.CASCADE,
        related_name='media_files',
    )
    file = models.FileField(upload_to='evidence/witness/media/')
    media_type = models.CharField(max_length=16, choices=MEDIA_CHOICES)
    uploaded_at = models.DateTimeField(auto_now_add=True)


class BiologicalEvidence(models.Model):
    """Biological: >=1 image required; verification_status; verification_result (nullable); editable by authorized roles only."""
    STATUS_PENDING = 'pending'
    STATUS_VERIFIED_FORENSIC = 'verified_forensic'
    STATUS_VERIFIED_NATIONAL_DB = 'verified_national_db'
    STATUS_REJECTED = 'rejected'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_VERIFIED_FORENSIC, 'Verified (Forensic)'),
        (STATUS_VERIFIED_NATIONAL_DB, 'Verified (National DB)'),
        (STATUS_REJECTED, 'Rejected'),
    ]

    evidence = models.OneToOneField(
        Evidence,
        on_delete=models.CASCADE,
        related_name='biological_detail',
    )
    verification_status = models.CharField(
        max_length=32,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
    )
    verification_result = models.TextField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_biological_evidence',
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)


class BiologicalEvidenceImage(models.Model):
    """Images attached to biological evidence (>=1 required)."""
    biological_evidence = models.ForeignKey(
        BiologicalEvidence,
        on_delete=models.CASCADE,
        related_name='images',
    )
    image = models.ImageField(upload_to='evidence/biological/')
    caption = models.CharField(max_length=255, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)


class VehicleEvidence(models.Model):
    """Vehicle: model, color; exactly one of license_plate or serial_number."""
    evidence = models.OneToOneField(
        Evidence,
        on_delete=models.CASCADE,
        related_name='vehicle_detail',
    )
    model = models.CharField(max_length=128, blank=True)
    color = models.CharField(max_length=64, blank=True)
    license_plate = models.CharField(max_length=32, blank=True)
    serial_number = models.CharField(max_length=64, blank=True)

    def clean(self):
        has_plate = bool(self.license_plate and self.license_plate.strip())
        has_serial = bool(self.serial_number and self.serial_number.strip())
        if has_plate and has_serial:
            raise ValidationError('Provide exactly one of license_plate or serial_number, not both.')
        if not has_plate and not has_serial:
            raise ValidationError('Provide exactly one of license_plate or serial_number.')


class IDDocumentEvidence(models.Model):
    """ID document: owner_full_name, attributes (JSON key-value, optional)."""
    evidence = models.OneToOneField(
        Evidence,
        on_delete=models.CASCADE,
        related_name='id_document_detail',
    )
    owner_full_name = models.CharField(max_length=255, blank=True)
    attributes = models.JSONField(default=dict, blank=True)


class EvidenceLink(models.Model):
    """Detective links related evidence (visual board)."""
    case = models.ForeignKey(
        'cases.Case',
        on_delete=models.CASCADE,
        related_name='evidence_links',
    )
    evidence_from = models.ForeignKey(
        Evidence,
        on_delete=models.CASCADE,
        related_name='links_from',
    )
    evidence_to = models.ForeignKey(
        Evidence,
        on_delete=models.CASCADE,
        related_name='links_to',
    )
    link_type = models.CharField(max_length=64, blank=True, default='red')  # red = connection line on detective board
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='evidence_links_created',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [['evidence_from', 'evidence_to']]
        indexes = [
            models.Index(fields=['case']),
        ]
