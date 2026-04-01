from django.contrib import admin
from .models import MenuPermission


@admin.register(MenuPermission)
class MenuPermissionAdmin(admin.ModelAdmin):
    list_display = ["login_user_id", "dashboard", "col_reports", "um_users", "um_roles", "updated_at"]