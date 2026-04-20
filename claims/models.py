from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Claim(models.Model):

    EXPENSE_TYPE_CHOICES = [
        ("self_expense",    "Self Expense"),
        ("travel_expense",  "Travel Expense"),
        ("food_expense",    "Food Expense"),
        ("accommodation",   "Accommodation Expense"),
        ("fuel",            "Fuel Expense"),
        ("parking",         "Parking Expense"),
        ("toll",            "Toll Expense"),
    ]

    DEPARTMENT_CHOICES = [
        ("engineering", "Engineering"),
        ("marketing",   "Marketing"),
        ("sales",       "Sales"),
        ("hr",          "Human Resources"),
        ("finance",     "Finance"),
        ("operations",  "Operations"),
        ("design",      "Design"),
    ]

    STATUS_CHOICES = [
        ("Pending",  "Pending"),
        ("Approved", "Approved"),
        ("Rejected", "Rejected"),
        ("Draft",    "Draft"),
    ]

    # Core fields
    claimed_by   = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="claims",
    )
    expense_type = models.CharField(max_length=30, choices=EXPENSE_TYPE_CHOICES)
    department   = models.CharField(max_length=20, choices=DEPARTMENT_CHOICES)
    client_name  = models.CharField(max_length=255)
    purpose      = models.CharField(max_length=500)
    amount       = models.DecimalField(max_digits=10, decimal_places=2)
    notes        = models.TextField(blank=True, default="")
    receipt      = models.FileField(
        upload_to="claims/receipts/%Y/%m/",
        null=True,
        blank=True,
    )
    status       = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default="Pending",
    )

    # Timestamps
    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Claim"
        verbose_name_plural = "Claims"

    def __str__(self):
        return f"[{self.status}] {self.client_name} – ₹{self.amount} ({self.get_expense_type_display()})"