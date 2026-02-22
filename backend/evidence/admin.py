from django.contrib import admin
from .models import Evidence, WitnessEvidence, BiologicalEvidence, BiologicalEvidenceImage, VehicleEvidence, IDDocumentEvidence, EvidenceLink


class BiologicalEvidenceImageInline(admin.TabularInline):
    model = BiologicalEvidenceImage
    extra = 0


@admin.register(Evidence)
class EvidenceAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'case', 'evidence_type', 'recorder', 'date_recorded']


@admin.register(WitnessEvidence)
class WitnessEvidenceAdmin(admin.ModelAdmin):
    list_display = ['evidence', 'statement']


@admin.register(BiologicalEvidence)
class BiologicalEvidenceAdmin(admin.ModelAdmin):
    list_display = ['evidence', 'validity_status', 'reviewed_by', 'reviewed_at']
    inlines = [BiologicalEvidenceImageInline]


@admin.register(VehicleEvidence)
class VehicleEvidenceAdmin(admin.ModelAdmin):
    list_display = ['evidence', 'plate_number', 'serial_number']


@admin.register(IDDocumentEvidence)
class IDDocumentEvidenceAdmin(admin.ModelAdmin):
    list_display = ['evidence']


@admin.register(EvidenceLink)
class EvidenceLinkAdmin(admin.ModelAdmin):
    list_display = ['evidence_from', 'evidence_to', 'link_type', 'case', 'created_by']
