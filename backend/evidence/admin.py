from django.contrib import admin
from .models import (
    Evidence,
    WitnessEvidence,
    WitnessMedia,
    BiologicalEvidence,
    BiologicalEvidenceImage,
    VehicleEvidence,
    IDDocumentEvidence,
    EvidenceLink,
)


class WitnessMediaInline(admin.TabularInline):
    model = WitnessMedia
    extra = 0


class BiologicalEvidenceImageInline(admin.TabularInline):
    model = BiologicalEvidenceImage
    extra = 0


@admin.register(Evidence)
class EvidenceAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'case', 'evidence_type', 'recorder', 'created_at']


@admin.register(WitnessEvidence)
class WitnessEvidenceAdmin(admin.ModelAdmin):
    list_display = ['evidence', 'transcript']
    inlines = [WitnessMediaInline]


@admin.register(BiologicalEvidence)
class BiologicalEvidenceAdmin(admin.ModelAdmin):
    list_display = ['evidence', 'verification_status', 'reviewed_by', 'reviewed_at']
    inlines = [BiologicalEvidenceImageInline]


@admin.register(VehicleEvidence)
class VehicleEvidenceAdmin(admin.ModelAdmin):
    list_display = ['evidence', 'model', 'color', 'license_plate', 'serial_number']


@admin.register(IDDocumentEvidence)
class IDDocumentEvidenceAdmin(admin.ModelAdmin):
    list_display = ['evidence', 'owner_full_name']


@admin.register(EvidenceLink)
class EvidenceLinkAdmin(admin.ModelAdmin):
    list_display = ['evidence_from', 'evidence_to', 'link_type', 'case', 'created_by']
