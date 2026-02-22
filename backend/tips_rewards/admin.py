from django.contrib import admin
from .models import Tip, Reward


@admin.register(Tip)
class TipAdmin(admin.ModelAdmin):
    list_display = ['id', 'submitter', 'title', 'status', 'created_at']


@admin.register(Reward)
class RewardAdmin(admin.ModelAdmin):
    list_display = ['id', 'unique_code', 'recipient_national_id', 'amount_rials', 'claimed', 'created_at']
