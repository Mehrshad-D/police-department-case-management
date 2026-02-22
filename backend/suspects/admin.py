from django.contrib import admin
from .models import Suspect, Interrogation, ArrestOrder


@admin.register(Suspect)
class SuspectAdmin(admin.ModelAdmin):
    list_display = ['id', 'case', 'user', 'status', 'proposed_by_detective', 'approved_by_supervisor', 'marked_at']


@admin.register(Interrogation)
class InterrogationAdmin(admin.ModelAdmin):
    list_display = ['id', 'suspect', 'detective_probability', 'supervisor_probability', 'chief_confirmed', 'created_at']


@admin.register(ArrestOrder)
class ArrestOrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'suspect', 'issued_by', 'order_type', 'issued_at']
