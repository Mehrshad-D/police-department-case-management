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
    """Final verdict and punishment (title + description)."""
    trial = models.OneToOneField(
        Trial,
        on_delete=models.CASCADE,
        related_name='verdict',
    )
    title = models.CharField(max_length=255)
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
