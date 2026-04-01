from django.contrib import admin
from .models import Branch, User


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display  = ["id", "name", "created_at"]
    search_fields = ["name"]
    ordering      = ["name"]


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display   = ["id", "username", "role", "status", "branch", "created_at"]
    list_filter    = ["role", "status", "branch"]
    search_fields  = ["username"]
    ordering       = ["-created_at"]
    readonly_fields = ["created_at", "updated_at"]