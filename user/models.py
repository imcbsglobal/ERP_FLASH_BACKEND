from django.db import models


class Branch(models.Model):
    name = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "branches"
        ordering = ["name"]

    def __str__(self):
        return self.name


class User(models.Model):
    ROLE_CHOICES = [
        ("Admin",    "Admin"),
        ("Manager",  "Manager"),
        ("Operator", "Operator"),
        ("Viewer",   "Viewer"),
        ("Support",  "Support"),
        ("Auditor",  "Auditor"),
    ]

    STATUS_CHOICES = [
        ("Active",   "Active"),
        ("Inactive", "Inactive"),
    ]

    username   = models.CharField(max_length=150, unique=True)
    address    = models.TextField()
    phone      = models.CharField(max_length=20)
    password   = models.CharField(max_length=255)
    branch     = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, related_name="users")
    role       = models.CharField(max_length=20, choices=ROLE_CHOICES)
    status     = models.CharField(max_length=10, choices=STATUS_CHOICES, default="Active")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "users"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.username} ({self.role})"