from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Role


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'created_at']
    search_fields = ['name']


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'full_name', 'national_id', 'is_active', 'date_joined']
    list_filter = ['is_active', 'is_staff', 'roles']
    search_fields = ['username', 'email', 'national_id', 'phone', 'full_name']
    filter_horizontal = ['roles']
    fieldsets = BaseUserAdmin.fieldsets + (
        (None, {'fields': ('phone', 'full_name', 'national_id', 'roles')}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        (None, {'fields': ('email', 'phone', 'full_name', 'national_id')}),
    )
