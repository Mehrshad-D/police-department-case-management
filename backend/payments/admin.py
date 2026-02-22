from django.contrib import admin
from .models import BailPayment, FinePayment


@admin.register(BailPayment)
class BailPaymentAdmin(admin.ModelAdmin):
    list_display = ['id', 'suspect', 'amount_rials', 'status', 'approved_by_supervisor', 'created_at']


@admin.register(FinePayment)
class FinePaymentAdmin(admin.ModelAdmin):
    list_display = ['id', 'trial', 'payer', 'amount_rials', 'status', 'created_at']
