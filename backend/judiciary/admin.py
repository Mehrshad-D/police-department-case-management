from django.contrib import admin
from .models import Trial, Verdict


@admin.register(Trial)
class TrialAdmin(admin.ModelAdmin):
    list_display = ['id', 'case', 'judge', 'started_at', 'closed_at']


@admin.register(Verdict)
class VerdictAdmin(admin.ModelAdmin):
    list_display = ['id', 'trial', 'title', 'recorded_at']
