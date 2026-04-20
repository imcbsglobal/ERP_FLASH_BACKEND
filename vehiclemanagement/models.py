from django.db import models


class TravelTrip(models.Model):
    """
    Represents a single vehicle trip from start to end.
    Created when a driver starts a trip (StartTrip form).
    Updated when the driver ends a trip (EndTrip form).
    """

    STATUS_CHOICES = [
        ('ongoing', 'Ongoing'),
        ('completed', 'Completed'),
    ]

    SERVICE_CHOICES = [
        ('washing', 'Washing'),
        ('alignment', 'Alignment'),
        ('airChecking', 'Air Checking'),
        ('greaseOil', 'Grease / Oil'),
    ]

    # ── Vehicle info ──────────────────────────────────────────────
    vehicle_name        = models.CharField(max_length=150)
    registration_number = models.CharField(max_length=50)

    # ── Trip start info ───────────────────────────────────────────
    traveled_by      = models.CharField(max_length=150)
    purpose_of_trip  = models.CharField(max_length=255)
    date             = models.DateField()
    start_time       = models.TimeField()
    maintenance_cost = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    odometer_start   = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        help_text="Odometer reading at trip start (km)"
    )
    odometer_start_image = models.ImageField(
        upload_to='trips/odometer/start/', null=True, blank=True
    )

    # ── Services performed at start ───────────────────────────────
    # Stored as a comma-separated string; validated against SERVICE_CHOICES
    services = models.CharField(
        max_length=200, blank=True, default='',
        help_text="Comma-separated list of services performed (e.g. 'washing,alignment')"
    )

    # ── Trip end info (filled on EndTrip) ─────────────────────────
    end_date    = models.DateField(null=True, blank=True)
    end_time    = models.TimeField(null=True, blank=True)
    odometer_end = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        help_text="Odometer reading at trip end (km)"
    )
    distance_covered = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        help_text="Computed: odometer_end - odometer_start (km)"
    )
    fuel_cost = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    odometer_end_image = models.ImageField(
        upload_to='trips/odometer/end/', null=True, blank=True
    )

    # ── Status & audit ────────────────────────────────────────────
    status     = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ongoing')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', '-start_time']
        verbose_name = 'Travel Trip'
        verbose_name_plural = 'Travel Trips'

    def __str__(self):
        return f"{self.vehicle_name} | {self.date} | {self.traveled_by}"

    def save(self, *args, **kwargs):
        # Auto-compute distance when both odometer readings are present
        if self.odometer_end is not None and self.odometer_start is not None:
            diff = float(self.odometer_end) - float(self.odometer_start)
            self.distance_covered = max(0, diff)
        # Mark completed when end_time is recorded
        if self.end_time is not None:
            self.status = 'completed'
        super().save(*args, **kwargs)