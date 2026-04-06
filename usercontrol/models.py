from django.db import models
from login.models import User as LoginUser


class MenuPermission(models.Model):
    login_user  = models.OneToOneField(
        LoginUser,
        on_delete=models.CASCADE,
        related_name='menu_permissions',
        verbose_name="User",
        null=True,
    )
    # Dashboard
    dashboard   = models.BooleanField(default=False)
    # Collection
    col_reports = models.BooleanField(default=False)
    # Vehicle Management
    vm_trips    = models.BooleanField(default=False)
    vm_service  = models.BooleanField(default=False)
    # User Management
    um_users    = models.BooleanField(default=False)
    um_roles    = models.BooleanField(default=False)
    # Master
    mm_vehicle  = models.BooleanField(default=False)

    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "usercontrol_menupermission"
        verbose_name = "Menu Permission"
        verbose_name_plural = "Menu Permissions"

    def __str__(self):
        if self.login_user:
            return f"Permissions({self.login_user.username})"
        return f"Permissions(id={self.id})"

    def allowed_menus(self):
        keys = ["dashboard", "col_reports", "vm_trips", "vm_service", "um_users", "um_roles", "mm_vehicle"]
        return [k for k in keys if getattr(self, k, False)]