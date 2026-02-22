"""
Bail/Fine payment. Level 2-3 suspects may pay bail; level 3 requires supervisor approval.
Integration with payment gateway (external; we store status and reference).
"""
from django.db import models
from django.conf import settings


class BailPayment(models.Model):
    """Bail payment for level 2 or 3 suspects. Level 3 requires supervisor approval."""
    STATUS_PENDING = 'pending'
    STATUS_SUPERVISOR_APPROVAL_NEEDED = 'supervisor_approval_needed'  # Level 3
    STATUS_APPROVED = 'approved'
    STATUS_GATEWAY_PENDING = 'gateway_pending'
    STATUS_COMPLETED = 'completed'
    STATUS_FAILED = 'failed'
    STATUS_CANCELLED = 'cancelled'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_SUPERVISOR_APPROVAL_NEEDED, 'Supervisor Approval Needed'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_GATEWAY_PENDING, 'Gateway Pending'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_FAILED, 'Failed'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]

    suspect = models.ForeignKey(
        'suspects.Suspect',
        on_delete=models.CASCADE,
        related_name='bail_payments',
    )
    amount_rials = models.BigIntegerField()
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default=STATUS_PENDING)
    approved_by_supervisor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_bail_payments',
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    gateway_reference = models.CharField(max_length=255, blank=True)  # External payment gateway ID
    gateway_response = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']


class FinePayment(models.Model):
    """Fine payment (e.g. after verdict). Payment gateway integration."""
    STATUS_PENDING = 'pending'
    STATUS_GATEWAY_PENDING = 'gateway_pending'
    STATUS_COMPLETED = 'completed'
    STATUS_FAILED = 'failed'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_GATEWAY_PENDING, 'Gateway Pending'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_FAILED, 'Failed'),
    ]

    # Link to verdict or case as needed
    trial = models.ForeignKey(
        'judiciary.Trial',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='fine_payments',
    )
    payer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='fine_payments',
    )
    amount_rials = models.BigIntegerField()
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default=STATUS_PENDING)
    gateway_reference = models.CharField(max_length=255, blank=True)
    gateway_response = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
