from django.db import models
from login.models import User as LoginUser

MENU_KEY_CHOICES = [
    ("dashboard",   "Dashboard"),
    ("col_reports", "Payment Reports"),
    ("um_users",    "All Users"),
    ("um_roles",    "User Control"),
]

class MenuPermission(models.Model):
    # First make it nullable to allow data migration
    login_user = models.OneToOneField(
        LoginUser, 
        on_delete=models.CASCADE, 
        related_name='menu_permissions',
        verbose_name="User",
        null=True  # Temporarily allow null for migration
    )
    dashboard   = models.BooleanField(default=False)
    col_reports = models.BooleanField(default=False)
    um_users    = models.BooleanField(default=False)
    um_roles    = models.BooleanField(default=False)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Menu Permission"
        verbose_name_plural = "Menu Permissions"

    def __str__(self):
        if self.login_user:
            return f"Permissions({self.login_user.username})"
        return f"Permissions(login_user_id={self.id})"