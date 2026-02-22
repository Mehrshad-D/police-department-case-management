"""
Evidence management: base evidence + types (witness, biological, vehicle, ID doc, other).
All evidence: title, description, date, recorder.
Detective can link related evidence (visual board).
"""
from django.db import models
from django.conf import settings


class Evidence(models.Model):
    """Base evidence: title, description, date, recorder. Subtypes add specific fields."""
    TYPE_WITNESS = 'witness'
    TYPE_BIOLOGICAL = 'biological'
    TYPE_VEHICLE = 'vehicle'
    TYPE_ID_DOCUMENT = 'id_document'
    TYPE_OTHER = 'other'
    TYPE_CHOICES = [
        (TYPE_WITNESS, 'Witness Statement/Media'),
        (TYPE_BIOLOGICAL, 'Biological/Forensic'),
        (TYPE_VEHICLE, 'Vehicle'),
        (TYPE_ID_DOCUMENT, 'ID Document'),
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
    date_recorded = models.DateTimeField(auto_now_add=True)  # can be overridden
    recorder = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='recorded_evidence',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date_recorded', '-created_at']
        indexes = [
            models.Index(fields=['case', 'evidence_type']),
        ]
        verbose_name_plural = 'Evidence'

    def __str__(self):
        return f"{self.get_evidence_type_display()}: {self.title}"


class WitnessEvidence(models.Model):
    """Witness statements or media (file/URL)."""
    evidence = models.OneToOneField(
        Evidence,
        on_delete=models.CASCADE,
        related_name='witness_detail',
    )
    statement = models.TextField(blank=True)
    media_file = models.FileField(upload_to='evidence/witness/', blank=True, null=True)
    media_url = models.URLField(blank=True)


class BiologicalEvidence(models.Model):
    """Biological/forensic: images + later lab results. Forensic doctor approves/rejects."""
    STATUS_PENDING = 'pending'
    STATUS_APPROVED = 'approved'
    STATUS_REJECTED = 'rejected'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_REJECTED, 'Rejected'),
    ]

    evidence = models.OneToOneField(
        Evidence,
        on_delete=models.CASCADE,
        related_name='biological_detail',
    )
    lab_results = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_biological_evidence',
    )
    validity_status = models.CharField(
        max_length=16,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)


class BiologicalEvidenceImage(models.Model):
    """Images attached to biological evidence."""
    biological_evidence = models.ForeignKey(
        BiologicalEvidence,
        on_delete=models.CASCADE,
        related_name='images',
    )
    image = models.ImageField(upload_to='evidence/biological/')
    caption = models.CharField(max_length=255, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)


class VehicleEvidence(models.Model):
    """Vehicle: plate OR serial, not both (enforced in serializer/clean)."""
    evidence = models.OneToOneField(
        Evidence,
        on_delete=models.CASCADE,
        related_name='vehicle_detail',
    )
    plate_number = models.CharField(max_length=32, blank=True)
    serial_number = models.CharField(max_length=64, blank=True)
    make_model = models.CharField(max_length=128, blank=True)

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.plate_number and self.serial_number:
            raise ValidationError('Provide either plate_number or serial_number, not both.')
        if not self.plate_number and not self.serial_number:
            raise ValidationError('Provide either plate_number or serial_number.')


class IDDocumentEvidence(models.Model):
    """ID document: flexible key-value attributes."""
    evidence = models.OneToOneField(
        Evidence,
        on_delete=models.CASCADE,
        related_name='id_document_detail',
    )
    # Flexible attributes, e.g. {"document_type": "national_id", "number": "123..."}
    attributes = models.JSONField(default=dict)


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
    link_type = models.CharField(max_length=64, blank=True)  # e.g. 'supports', 'contradicts'
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
