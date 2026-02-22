"""
Suspect management: proposal, interrogation, guilt probability, arrest, status tracking.
Detective proposes -> supervisor reviews with criminal records -> approve (arrest) or reject.
"""
from django.db import models
from django.conf import settings
from django.utils import timezone


class Suspect(models.Model):
    """Suspect linked to a case. Status: under pursuit -> arrested -> etc."""
    STATUS_UNDER_PURSUIT = 'under_pursuit'
    STATUS_HIGH_PRIORITY = 'high_priority'  # After >1 month
    STATUS_ARRESTED = 'arrested'
    STATUS_RELEASED = 'released'
    STATUS_CONVICTED = 'convicted'
    STATUS_CHOICES = [
        (STATUS_UNDER_PURSUIT, 'Under Pursuit'),
        (STATUS_HIGH_PRIORITY, 'High Priority'),
        (STATUS_ARRESTED, 'Arrested'),
        (STATUS_RELEASED, 'Released'),
        (STATUS_CONVICTED, 'Convicted'),
    ]

    case = models.ForeignKey(
        'cases.Case',
        on_delete=models.CASCADE,
        related_name='suspects',
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='suspect_in_cases',
    )
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default=STATUS_UNDER_PURSUIT)
    proposed_by_detective = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='proposed_suspects',
    )
    approved_by_supervisor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_suspects',
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    marked_at = models.DateTimeField(auto_now_add=True)  # When marked as suspect
    # For public listing: ranking_score = max(days_pursued) * max(crime_severity); reward = score * 20_000_000
    first_pursuit_date = models.DateTimeField(auto_now_add=True)  # When status became under_pursuit

    class Meta:
        unique_together = [['case', 'user']]
        ordering = ['-marked_at']
        indexes = [
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"Suspect: {self.user} in Case #{self.case_id}"

    @property
    def days_pursued(self):
        if self.status not in (self.STATUS_UNDER_PURSUIT, self.STATUS_HIGH_PRIORITY):
            return 0
        delta = timezone.now() - self.first_pursuit_date
        return max(0, delta.days)

    def update_high_priority(self):
        """If under_pursuit and >1 month, set high_priority."""
        if self.status == self.STATUS_UNDER_PURSUIT and self.days_pursued >= 31:
            self.status = self.STATUS_HIGH_PRIORITY
            self.save(update_fields=['status'])


class Interrogation(models.Model):
    """
    Detective and supervisor each assign guilt probability (1-10).
    Captain issues final decision. For critical crimes, police chief must confirm.
    """
    suspect = models.ForeignKey(
        Suspect,
        on_delete=models.CASCADE,
        related_name='interrogations',
    )
    detective_probability = models.PositiveSmallIntegerField(null=True, blank=True)  # 1-10
    supervisor_probability = models.PositiveSmallIntegerField(null=True, blank=True)  # 1-10
    captain_decision = models.TextField(blank=True)  # Final decision notes
    captain_decided_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='interrogation_decisions',
    )
    captain_decided_at = models.DateTimeField(null=True, blank=True)
    chief_confirmed = models.BooleanField(default=False)  # For critical crimes
    chief_confirmed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='interrogation_chief_confirmations',
    )
    chief_confirmed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']


class ArrestOrder(models.Model):
    """Sergeant issues arrest/interrogation order; links to suspect."""
    suspect = models.ForeignKey(
        Suspect,
        on_delete=models.CASCADE,
        related_name='arrest_orders',
    )
    issued_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='issued_arrest_orders',
    )
    order_type = models.CharField(max_length=32)  # e.g. 'arrest', 'interrogation'
    notes = models.TextField(blank=True)
    issued_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-issued_at']
