"""
Case, Complaint, Crime Scene and case creation workflow.
"""
from django.db import models
from django.conf import settings


class Case(models.Model):
    """
    Central case entity. Created from complaint (after validation) or by officer (crime scene).
    """
    SEVERITY_LEVEL_3 = 3   # Minor (petty theft, minor fraud)
    SEVERITY_LEVEL_2 = 2   # Moderate (e.g. car theft)
    SEVERITY_LEVEL_1 = 1   # Major (e.g. murder)
    SEVERITY_CRISIS = 0    # Extreme (serial murder, assassination)
    SEVERITY_CHOICES = [
        (SEVERITY_LEVEL_3, 'Level 3 - Minor'),
        (SEVERITY_LEVEL_2, 'Level 2 - Moderate'),
        (SEVERITY_LEVEL_1, 'Level 1 - Major'),
        (SEVERITY_CRISIS, 'Crisis - Extreme'),
    ]

    STATUS_OPEN = 'open'
    STATUS_UNDER_INVESTIGATION = 'under_investigation'
    STATUS_WAITING_SERGEANT_APPROVAL = 'waiting_sergeant_approval'
    STATUS_PENDING_APPROVAL = 'pending_approval'
    STATUS_REFERRED_TO_JUDICIARY = 'referred_to_judiciary'
    STATUS_CLOSED = 'closed'
    STATUS_CHOICES = [
        (STATUS_OPEN, 'Open'),
        (STATUS_UNDER_INVESTIGATION, 'Under Investigation'),
        (STATUS_WAITING_SERGEANT_APPROVAL, 'Waiting Sergeant Approval'),
        (STATUS_PENDING_APPROVAL, 'Pending Approval'),
        (STATUS_REFERRED_TO_JUDICIARY, 'Referred to Judiciary'),
        (STATUS_CLOSED, 'Closed'),
    ]

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    severity = models.PositiveSmallIntegerField(choices=SEVERITY_CHOICES, default=SEVERITY_LEVEL_3)
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default=STATUS_OPEN)
    is_crime_scene_case = models.BooleanField(default=False)  # No complainant initially
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_cases',
    )
    assigned_detective = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_cases',
    )
    approved_by_captain = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_cases',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['severity']),
        ]

    def __str__(self):
        return f"{self.title} (#{self.pk})"


class Complaint(models.Model):
    """
    Complaint submitted by complainant. Validation: trainee review -> officer approval.
    Trainee can return for correction (with error message); after 3 failed corrections, case rejected.
    """
    STATUS_DRAFT = 'draft'
    STATUS_PENDING_TRAINEE = 'pending_trainee'
    STATUS_CORRECTION_NEEDED = 'correction_needed'
    STATUS_PENDING_OFFICER = 'pending_officer'
    STATUS_APPROVED = 'approved'
    STATUS_REJECTED = 'rejected'
    STATUS_CHOICES = [
        (STATUS_DRAFT, 'Draft'),
        (STATUS_PENDING_TRAINEE, 'Pending Trainee Review'),
        (STATUS_CORRECTION_NEEDED, 'Correction Needed'),
        (STATUS_PENDING_OFFICER, 'Pending Officer Approval'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_REJECTED, 'Rejected'),
    ]

    complainant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='complaints_submitted',
    )
    title = models.CharField(max_length=255)
    description = models.TextField()
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    correction_count = models.PositiveSmallIntegerField(default=0)  # After 3, reject
    last_correction_message = models.TextField(blank=True)  # Error message from trainee
    reviewed_by_trainee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='complaints_reviewed_as_trainee',
    )
    reviewed_by_officer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='complaints_approved_by_officer',
    )
    case = models.OneToOneField(
        Case,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='complaint_origin',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Complaint: {self.title} ({self.get_status_display()})"


class CaseComplainant(models.Model):
    """Multiple complainants per case (M2M with optional role/notes)."""
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name='complainants')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='cases_as_complainant')
    is_primary = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [['case', 'user']]


class CrimeSceneReport(models.Model):
    """
    Officer records time/date and witnesses. Requires supervisor approval unless created by chief.
    Initially no complainant; case can gain complainants later.
    """
    case = models.OneToOneField(Case, on_delete=models.CASCADE, related_name='crime_scene_report')
    reported_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='crime_scene_reports',
    )
    scene_datetime = models.DateTimeField()
    location_description = models.TextField(blank=True)
    witnesses_contact_info = models.TextField(blank=True)  # Free text or structured later
    approved_by_supervisor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_crime_scene_reports',
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
