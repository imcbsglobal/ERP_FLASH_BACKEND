from django.db import models


class VehicleMaster(models.Model):

    # ── Choices ────────────────────────────────────────────────────
    VEHICLE_TYPE_CHOICES = [
        ("Car",   "Car"),
        ("Bike",  "Bike"),
        ("Truck", "Truck"),
        ("Bus",   "Bus"),
        ("Van",   "Van"),
        ("Other", "Other"),
    ]

    OWNERSHIP_CHOICES = [
        ("Personal", "Personal"),
        ("Company",  "Company"),
        ("Leased",   "Leased"),
        ("Rental",   "Rental"),
    ]

    FUEL_TYPE_CHOICES = [
        ("Petrol",   "Petrol"),
        ("Diesel",   "Diesel"),
        ("Electric", "Electric"),
        ("Hybrid",   "Hybrid"),
        ("CNG",      "CNG"),
    ]

    STATUS_CHOICES = [
        ("Active",   "Active"),
        ("Inactive", "Inactive"),
    ]

    # ── Basic Information ──────────────────────────────────────────
    vehicle_name        = models.CharField(max_length=100)
    company_brand       = models.CharField(max_length=100, blank=True, null=True)
    registration_number = models.CharField(max_length=50, unique=True)
    vehicle_type        = models.CharField(max_length=20, choices=VEHICLE_TYPE_CHOICES, blank=True, null=True)
    ownership           = models.CharField(max_length=20, choices=OWNERSHIP_CHOICES, blank=True, null=True)
    fuel_type           = models.CharField(max_length=20, choices=FUEL_TYPE_CHOICES, blank=True, null=True)
    vehicle_photo       = models.ImageField(upload_to="vehicles/photos/", blank=True, null=True)

    # ── Ownership & Insurance ──────────────────────────────────────
    owner_name              = models.CharField(max_length=150)
    insurance_no            = models.CharField(max_length=100, blank=True, null=True)
    insurance_expired_date  = models.DateField(blank=True, null=True)
    pollution_expired_date  = models.DateField(blank=True, null=True)

    # ── Maintenance ────────────────────────────────────────────────
    last_service_date = models.DateField(blank=True, null=True)
    next_service_date = models.DateField(blank=True, null=True)
    current_odometer  = models.PositiveIntegerField(default=0)          # in km

    # ── Technical ─────────────────────────────────────────────────
    chassis_number = models.CharField(max_length=100, blank=True, null=True)
    engine_number  = models.CharField(max_length=100, blank=True, null=True)

    # ── Additional ────────────────────────────────────────────────
    note = models.TextField(blank=True, null=True)

    # ── Meta ───────────────────────────────────────────────────────
    status      = models.CharField(max_length=10, choices=STATUS_CHOICES, default="Active")
    total_trips = models.PositiveIntegerField(default=0)                # incremented externally
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        db_table        = "vehicle_master"
        verbose_name    = "Vehicle Master"
        verbose_name_plural = "Vehicle Masters"
        ordering        = ["-created_at"]

    def __str__(self):
        return f"{self.vehicle_name} ({self.registration_number})"