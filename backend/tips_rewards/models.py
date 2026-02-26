"""
Public tips and rewards. Citizens submit tips; officer reviews -> detective confirms -> reward code.
Police view reward info via national_id + code. Reward = ranking_score * 20,000,000 rials (for suspects).
"""
from django.db import models
from django.conf import settings
import uuid


class Tip(models.Model):
    """Citizen-submitted tip."""
    STATUS_PENDING = 'pending'
    STATUS_OFFICER_REVIEWED = 'officer_reviewed'
    STATUS_DETECTIVE_CONFIRMED = 'detective_confirmed'
    STATUS_REJECTED = 'rejected'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_OFFICER_REVIEWED, 'Officer Reviewed'),
        (STATUS_DETECTIVE_CONFIRMED, 'Detective Confirmed'),
        (STATUS_REJECTED, 'Rejected'),
    ]

    submitter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='submitted_tips',
    )
    case = models.ForeignKey(
        'cases.Case',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='tips',
    )
    suspect = models.ForeignKey(
        'suspects.Suspect',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='tips',
    )
    title = models.CharField(max_length=255)
    description = models.TextField()
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default=STATUS_PENDING)
    reviewed_by_officer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tips_reviewed_by_officer',
    )
    reviewed_by_detective = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tips_confirmed_by_detective',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']


class Reward(models.Model):
    """Reward for tip or for suspect listing. Claimable with national_id + unique code."""
    tip = models.OneToOneField(
        Tip,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reward',
    )
    suspect = models.ForeignKey(
        'suspects.Suspect',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='rewards',
    )
    amount_rials = models.BigIntegerField()  # 20_000_000 * score for suspect rewards
    unique_code = models.CharField(max_length=64, unique=True, db_index=True)
    recipient_national_id = models.CharField(max_length=32, db_index=True)
    claimed = models.BooleanField(default=False)
    claimed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient_national_id', 'unique_code']),
        ]

    def save(self, *args, **kwargs):
        if not self.unique_code:
            self.unique_code = str(uuid.uuid4()).replace('-', '')[:24]
        super().save(*args, **kwargs)


class RewardPayment(models.Model):
    """Payment record when police marks reward as paid at office."""
    reward = models.ForeignKey(
        Reward,
        on_delete=models.CASCADE,
        related_name='payments',
    )
    officer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='reward_payments_made',
    )
    amount_rials = models.BigIntegerField()
    paid_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-paid_at']
