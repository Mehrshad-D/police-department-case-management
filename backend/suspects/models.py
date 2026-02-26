from django.db import models
from django.conf import settings
from django.utils import timezone

class Suspect(models.Model):
    STATUS_UNDER_PURSUIT = 'under_pursuit'
    STATUS_HIGH_PRIORITY = 'high_priority'
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
    marked_at = models.DateTimeField(auto_now_add=True)
    first_pursuit_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [['case', 'user']]
        ordering = ['-marked_at']
        indexes = [
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.user} - {self.case_id}"

    @property
    def days_under_investigation(self):
        """Days since marked as suspect while under investigation or most_wanted."""
        if self.status not in (self.STATUS_UNDER_INVESTIGATION, self.STATUS_MOST_WANTED):
            return 0
        delta = timezone.now() - self.first_pursuit_date
        return max(0, delta.days)

    @property
    def ranking_score(self):
        suspects_for_user = Suspect.objects.filter(user=self.user)
        max_days = 0
        for s in suspects_for_user.filter(case__status__in=['open', 'under_investigation']):
            if s.status in [self.STATUS_UNDER_PURSUIT, self.STATUS_HIGH_PRIORITY]:
                delta = timezone.now() - s.first_pursuit_date
                days = max(0, delta.days)
                if days > max_days:
                    max_days = days

        max_severity = 0
        for s in suspects_for_user:
            sev_val = 4 - s.case.severity
            if sev_val > max_severity:
                max_severity = sev_val
        
        return max_days * max_severity

    @property
    def reward_amount(self):
        return self.ranking_score * 20000000

    def update_high_priority(self):
        if self.status == self.STATUS_UNDER_PURSUIT and self.days_pursued >= 31:
            self.status = self.STATUS_HIGH_PRIORITY
            self.save(update_fields=['status'])

    def mark_released(self):
        self.status = self.STATUS_RELEASED
        self.save(update_fields=['status'])

    def mark_convicted(self):
        self.status = self.STATUS_CONVICTED
        self.save(update_fields=['status'])


class Interrogation(models.Model):
    suspect = models.ForeignKey(
        Suspect,
        on_delete=models.CASCADE,
        related_name='interrogations',
    )
    detective_probability = models.PositiveSmallIntegerField(null=True, blank=True)
    supervisor_probability = models.PositiveSmallIntegerField(null=True, blank=True)
    captain_decision = models.TextField(blank=True)
    captain_decided_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='interrogation_decisions',
    )
    captain_decided_at = models.DateTimeField(null=True, blank=True)
    chief_confirmed = models.BooleanField(default=False)
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
    order_type = models.CharField(max_length=32)
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
