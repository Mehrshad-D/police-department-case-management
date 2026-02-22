from django.contrib import admin
from .models import Case, Complaint, CaseComplainant, CrimeSceneReport


@admin.register(Case)
class CaseAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'severity', 'status', 'is_crime_scene_case', 'created_by', 'created_at']
    list_filter = ['status', 'severity', 'is_crime_scene_case']


@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'complainant', 'status', 'correction_count', 'created_at']
    list_filter = ['status']


@admin.register(CaseComplainant)
class CaseComplainantAdmin(admin.ModelAdmin):
    list_display = ['case', 'user', 'is_primary', 'added_at']


@admin.register(CrimeSceneReport)
class CrimeSceneReportAdmin(admin.ModelAdmin):
    list_display = ['id', 'case', 'reported_by', 'approved_by_supervisor', 'scene_datetime', 'created_at']
