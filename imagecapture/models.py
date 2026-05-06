import uuid
from django.db import models


class Customer(models.Model):
    """
    Customer record — populated from Image_link.jsx customer list /
    manual entry. Mirrors the customers[] array in imgcapture_list.jsx.
    """
    name    = models.CharField(max_length=255)
    phone   = models.CharField(max_length=20)
    branch  = models.CharField(max_length=100, blank=True)
    email   = models.EmailField(blank=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.phone})"


class CaptureLink(models.Model):
    """
    One-time UUID link generated for a customer in Image_link.jsx
    handleGenerate(). The UUID becomes the URL path:
        /image_capture/capture/<uuid>/
    """
    STATUS_PENDING  = "pending"
    STATUS_USED     = "used"
    STATUS_EXPIRED  = "expired"
    STATUS_CHOICES  = [
        (STATUS_PENDING, "Pending"),
        (STATUS_USED,    "Used"),
        (STATUS_EXPIRED, "Expired"),
    ]

    uuid          = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    customer      = models.ForeignKey(
        Customer,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="capture_links",
    )
    # Fallback when staff enters a name manually (no FK customer)
    customer_name = models.CharField(max_length=255, blank=True)
    phone         = models.CharField(max_length=20)
    status        = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_PENDING)
    created_at    = models.DateTimeField(auto_now_add=True)
    expires_at    = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Link → {self.effective_name} [{self.status}]"

    @property
    def effective_name(self):
        """Return customer name from FK or manual field."""
        if self.customer_id:
            return self.customer.name
        return self.customer_name or ""

    @property
    def link_path(self):
        return f"/image_capture/capture/{self.uuid}/"


class OtpRecord(models.Model):
    """
    Tracks every OTP send + verification attempt.
    phoneverify.jsx  → send
    Otp_verification.jsx → verify / resend
    """
    STATUS_SENT     = "sent"
    STATUS_VERIFIED = "verified"
    STATUS_EXPIRED  = "expired"
    STATUS_FAILED   = "failed"
    STATUS_CHOICES  = [
        (STATUS_SENT,     "Sent"),
        (STATUS_VERIFIED, "Verified"),
        (STATUS_EXPIRED,  "Expired"),
        (STATUS_FAILED,   "Failed"),
    ]

    capture_link = models.ForeignKey(
        CaptureLink,
        on_delete=models.CASCADE,
        related_name="otp_records",
        null=True, blank=True,
    )
    phone       = models.CharField(max_length=20)
    otp_code    = models.CharField(max_length=10)
    status      = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_SENT)
    attempts    = models.PositiveSmallIntegerField(default=0)
    created_at  = models.DateTimeField(auto_now_add=True)
    verified_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"OTP {self.phone} [{self.status}]"


class ImageCapture(models.Model):
    """
    Final submitted capture record.
    Created by Image_add.jsx handleUpload() (POST /api/upload-image/).
    Displayed in imgcapture_list.jsx table and verify_success.jsx.
    """
    # ── Verification status (system-set) ──────────────────────────
    VS_VERIFIED = "verified"
    VS_PENDING  = "pending"
    VS_FAILED   = "failed"
    VERIFICATION_STATUS_CHOICES = [
        (VS_VERIFIED, "Verified"),
        (VS_PENDING,  "Pending"),
        (VS_FAILED,   "Failed"),
    ]

    # ── Manual status (staff-set) ─────────────────────────────────
    MS_PENDING      = "pending"
    MS_APPROVED     = "approved"
    MS_UNDER_REVIEW = "under_review"
    MS_REJECTED     = "rejected"
    MANUAL_STATUS_CHOICES = [
        (MS_PENDING,      "Pending"),
        (MS_APPROVED,     "Approved"),
        (MS_UNDER_REVIEW, "Under Review"),
        (MS_REJECTED,     "Rejected"),
    ]

    capture_link        = models.ForeignKey(
        CaptureLink,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="captures",
    )
    customer_name       = models.CharField(max_length=255, blank=True)
    phone               = models.CharField(max_length=20, blank=True)

    # Image file — saved to media/captures/YYYY/MM/DD/
    image               = models.ImageField(upload_to="captures/%Y/%m/%d/")

    # GPS data from Image_capture.jsx reverseGeocode()
    latitude            = models.DecimalField(max_digits=18, decimal_places=15, null=True, blank=True)
    longitude           = models.DecimalField(max_digits=18, decimal_places=15, null=True, blank=True)
    address             = models.TextField(blank=True)

    verification_status = models.CharField(
        max_length=10,
        choices=VERIFICATION_STATUS_CHOICES,
        default=VS_VERIFIED,
    )
    manual_status       = models.CharField(
        max_length=15,
        choices=MANUAL_STATUS_CHOICES,
        default=MS_PENDING,
    )

    verified_at = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-verified_at"]

    def __str__(self):
        return f"Capture: {self.customer_name or self.phone} @ {self.verified_at:%Y-%m-%d %H:%M}"