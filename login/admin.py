from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display    = ('email', 'full_name', 'role', 'is_active', 'is_staff', 'date_joined')
    list_filter     = ('role', 'is_active', 'is_staff')
    search_fields   = ('email', 'first_name', 'last_name')
    ordering        = ('-date_joined',)

    fieldsets = (
        (None,           {'fields': ('email', 'password')}),
        ('Personal Info',{'fields': ('first_name', 'last_name')}),
        ('Role & Access',{'fields': ('role', 'is_active', 'is_staff', 'is_superuser')}),
        ('Permissions',  {'fields': ('groups', 'user_permissions')}),
        ('Timestamps',   {'fields': ('date_joined', 'last_login'), 'classes': ('collapse',)}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields':  ('email', 'first_name', 'last_name', 'role', 'password1', 'password2'),
        }),
    )

    readonly_fields = ('date_joined', 'last_login')

    # Email is used instead of username
    filter_horizontal = ('groups', 'user_permissions')