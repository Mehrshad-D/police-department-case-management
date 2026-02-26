"""
Suspect management: proposal, interrogation, guilt probability, arrest, status tracking.
Detective proposes -> supervisor reviews with criminal records -> approve (arrest) or reject.
"""
from django.db import models
from django.conf import settings
from django.utils import timezone


class Suspect(models.Model):
    """Suspect linked to a case. Once added -> UNDER_INVESTIGATION; >30 days -> MOST_WANTED."""
    STATUS_UNDER_INVESTIGATION = 'under_investigation'
    STATUS_MOST_WANTED = 'most_wanted'  # Under investigation > 30 days
    STATUS_ARRESTED = 'arrested'
    STATUS_RELEASED = 'released'
    STATUS_CONVICTED = 'convicted'
    STATUS_REJECTED = 'rejected'
    STATUS_CHOICES = [
        (STATUS_UNDER_INVESTIGATION, 'Under Investigation'),
        (STATUS_MOST_WANTED, 'Most Wanted'),
        (STATUS_ARRESTED, 'Arrested'),
        (STATUS_RELEASED, 'Released'),
        (STATUS_CONVICTED, 'Convicted'),
        (STATUS_REJECTED, 'Rejected'),
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
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default=STATUS_UNDER_INVESTIGATION)
    rejection_message = models.TextField(blank=True)
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
    first_pursuit_date = models.DateTimeField(auto_now_add=True)  # When status became under_investigation

    class Meta:
        unique_together = [['case', 'user']]
        ordering = ['-marked_at']
        indexes = [
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"Suspect: {self.user} in Case #{self.case_id}"

    @property
    def days_under_investigation(self):
        """Days since marked as suspect while under investigation or most_wanted."""
        if self.status not in (self.STATUS_UNDER_INVESTIGATION, self.STATUS_MOST_WANTED):
            return 0
        delta = timezone.now() - self.first_pursuit_date
        return max(0, delta.days)

    @property
    def days_pursued(self):
        """Alias for ranking: same as days_under_investigation for under_investigation/most_wanted."""
        return self.days_under_investigation

    def crime_degree(self):
        """Crime severity 1-4: Level 3=1, Level 2=2, Level 1=3, Crisis=4."""
        from cases.models import Case
        # Case severity: 3=minor, 2=moderate, 1=major, 0=crisis -> degree 1,2,3,4
        return 4 - self.case.severity

    def ranking_score(self):
        """score = max(days_under_investigation) * max(crime_degree). For single case: days * crime_degree."""
        return self.days_under_investigation * self.crime_degree()

    def reward_rials(self):
        """reward = score * 20,000,000 (Rials)."""
        return self.ranking_score() * 20_000_000

    def update_most_wanted(self):
        """If under_investigation and >30 days, set most_wanted."""
        if self.status == self.STATUS_UNDER_INVESTIGATION and self.days_under_investigation > 30:
            self.status = self.STATUS_MOST_WANTED
            self.save(update_fields=['status'])

    def mark_released(self):
        self.status = self.STATUS_RELEASED
        self.save(update_fields=['status'])

    def mark_convicted(self):
        self.status = self.STATUS_CONVICTED
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
    notes = models.TextField(blank=True)
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


class CaptainDecision(models.Model):
    """Captain final decision after interrogation scores and evidence review. CRITICAL cases require ChiefApproval."""
    DECISION_GUILTY = 'guilty'
    DECISION_NOT_GUILTY = 'not_guilty'
    DECISION_CHOICES = [
        (DECISION_GUILTY, 'Guilty'),
        (DECISION_NOT_GUILTY, 'Not Guilty'),
    ]

    suspect = models.ForeignKey(
        Suspect,
        on_delete=models.CASCADE,
        related_name='captain_decisions',
    )
    case = models.ForeignKey(
        'cases.Case',
        on_delete=models.CASCADE,
        related_name='captain_decisions',
    )
    final_decision = models.CharField(max_length=16, choices=DECISION_CHOICES)
    reasoning = models.TextField(blank=True)
    decided_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='captain_decisions_made',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']


class ChiefApproval(models.Model):
    """Chief approval/rejection for captain decision when crime severity is CRITICAL."""
    STATUS_APPROVED = 'approved'
    STATUS_REJECTED = 'rejected'
    STATUS_CHOICES = [
        (STATUS_APPROVED, 'Approved'),
        (STATUS_REJECTED, 'Rejected'),
    ]

    captain_decision = models.OneToOneField(
        CaptainDecision,
        on_delete=models.CASCADE,
        related_name='chief_approval',
    )
    status = models.CharField(max_length=16, choices=STATUS_CHOICES)
    comment = models.TextField(blank=True)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='chief_approvals_given',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
