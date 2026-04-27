from django.db import models
from django.conf import settings
from vehiclemaster.models import VehicleMaster


OFFENCE_TYPE_CHOICES = [
    ("Signal Jumping", "Signal Jumping"),
    ("Over Speeding", "Over Speeding"),
    ("Drunk Driving", "Drunk Driving"),
    ("Wrong Parking", "Wrong Parking"),
    ("No Helmet", "No Helmet"),
    ("No Seatbelt", "No Seatbelt"),
    ("Using Mobile While Driving", "Using Mobile While Driving"),
    ("Overloading", "Overloading"),
    ("No License", "No License"),
    ("No Insurance", "No Insurance"),
    ("Triple Riding", "Triple Riding"),
    ("Lane Violation", "Lane Violation"),
    ("Other", "Other"),
]

PAYMENT_STATUS_CHOICES = [
    ("Pending", "Pending"),
    ("Paid", "Paid"),
    ("Waived", "Waived"),
]


class Challan(models.Model):
    vehicle         = models.ForeignKey(
                        VehicleMaster,
                        on_delete=models.PROTECT,
                        related_name="challans"
                    )
    # Track who created this challan (login.User — same model used across the app)
    created_by      = models.ForeignKey(
                        settings.AUTH_USER_MODEL,
                        on_delete=models.SET_NULL,
                        null=True, blank=True,
                        related_name="challans_created",
                    )
    date            = models.DateField(help_text="Default / entry date")
    challan_no      = models.CharField(max_length=100, unique=True)
    challan_date    = models.DateField()
    offence_type    = models.CharField(max_length=50, choices=OFFENCE_TYPE_CHOICES)
    location        = models.CharField(max_length=255)
    fine_amount     = models.DecimalField(max_digits=10, decimal_places=2)
    payment_status  = models.CharField(
                        max_length=20,
                        choices=PAYMENT_STATUS_CHOICES,
                        default="Pending"
                    )
    challan_doc     = models.FileField(
                        upload_to="challans/docs/",
                        null=True, blank=True
                    )
    payment_receipt = models.FileField(
                        upload_to="challans/receipts/",
                        null=True, blank=True
                    )
    remark          = models.TextField(blank=True, default="")
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "challan"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.challan_no} — {self.vehicle}"