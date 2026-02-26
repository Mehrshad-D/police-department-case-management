"""
Trial and verdict. Judge views full case history, reports, approvals, officers, evidence.
Final verdict and punishment stored with title/description.
"""
from django.db import models
from django.conf import settings


class Trial(models.Model):
    """Case referred to judiciary; judge records verdict and punishment."""
    case = models.OneToOneField(
        'cases.Case',
        on_delete=models.CASCADE,
        related_name='trial',
    )
    judge = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='presided_trials',
    )
    started_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-started_at']

    def __str__(self):
        return f"Trial for Case #{self.case_id}"


class Verdict(models.Model):
    """Judge records verdict (GUILTY/INNOCENT) and punishment (title + description)."""
    VERDICT_GUILTY = 'guilty'
    VERDICT_INNOCENT = 'innocent'
    VERDICT_CHOICES = [
        (VERDICT_GUILTY, 'Guilty'),
        (VERDICT_INNOCENT, 'Innocent'),
    ]

    trial = models.OneToOneField(
        Trial,
        on_delete=models.CASCADE,
        related_name='verdict',
    )
    verdict_type = models.CharField(max_length=16, choices=VERDICT_CHOICES, default=VERDICT_GUILTY)
    title = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    punishment_title = models.CharField(max_length=255, blank=True)
    punishment_description = models.TextField(blank=True)
    recorded_at = models.DateTimeField(auto_now_add=True)
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='recorded_verdicts',
    )

    class Meta:
        ordering = ['-recorded_at']
