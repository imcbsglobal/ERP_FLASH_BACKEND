import random
import string
import logging
from datetime import timedelta

from django.utils import timezone
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser

from .models import Customer, CaptureLink, OtpRecord, ImageCapture
from .serializers import (
    CustomerSerializer,
    CaptureLinkCreateSerializer,
    CaptureLinkDetailSerializer,
    CaptureLinkListSerializer,
    OtpSendSerializer,
    OtpVerifySerializer,
    OtpRecordReadSerializer,
    ImageCaptureUploadSerializer,
    ImageCaptureListSerializer,
    ImageCaptureDetailSerializer,
    ManualStatusUpdateSerializer,
)

logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────
OTP_EXPIRY_MINUTES = 5
OTP_MAX_ATTEMPTS   = 5
OTP_LENGTH         = 4   # 4-digit — matches Otp_verification.jsx CORRECT_OTP = "1234"


# ── Helpers ───────────────────────────────────────────────────────────────────

def _generate_otp(length: int = OTP_LENGTH) -> str:
    return "".join(random.choices(string.digits, k=length))


def _send_whatsapp_otp(phone: str, otp: str) -> None:
    """
    WhatsApp OTP delivery stub.
    Replace with your chosen provider (Twilio / 360dialog / Meta Cloud API).

    Example — Twilio WhatsApp:
        from twilio.rest import Client
        from django.conf import settings
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        client.messages.create(
            from_=f"whatsapp:{settings.TWILIO_WHATSAPP_FROM}",
            to=f"whatsapp:{phone}",
            body=f"Your verification OTP is *{otp}*. Valid for {OTP_EXPIRY_MINUTES} minutes.",
        )
    """
    logger.info("[WhatsApp OTP stub] phone=%s otp=%s", phone, otp)


# ══════════════════════════════════════════════════════════════════════════════
# Customer Views
# ══════════════════════════════════════════════════════════════════════════════

class CustomerListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/customers/           List customers (Image_link.jsx dropdown)
    POST /api/customers/           Create a customer
    Query params: branch, search
    """
    serializer_class = CustomerSerializer

    def get_queryset(self):
        qs     = Customer.objects.all()
        branch = self.request.query_params.get("branch", "").strip()
        search = self.request.query_params.get("search", "").strip()
        if branch and branch != "All Branches":
            qs = qs.filter(branch=branch)
        if search:
            qs = qs.filter(name__icontains=search)
        return qs


class CustomerDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET / PATCH / DELETE  /api/customers/<pk>/
    """
    queryset         = Customer.objects.all()
    serializer_class = CustomerSerializer


# ══════════════════════════════════════════════════════════════════════════════
# Capture Link Views
# ══════════════════════════════════════════════════════════════════════════════

class GenerateLinkView(generics.CreateAPIView):
    """
    POST /api/generate-link/
    Called by Image_link.jsx handleGenerate().

    Request body:
        { customer_id?, customer_name?, phone, expires_in_hours? (default 24) }

    Response adds link_full (absolute URL) on top of the serializer output.
    """
    serializer_class = CaptureLinkCreateSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        expires_in = int(request.data.get("expires_in_hours", 24))
        link = serializer.save(expires_at=timezone.now() + timedelta(hours=expires_in))

        # Return the richer detail serializer (includes link_path + resolved name)
        detail = CaptureLinkDetailSerializer(link, context={"request": request})
        payload = detail.data
        payload["link_full"] = request.build_absolute_uri(link.link_path)
        return Response(payload, status=status.HTTP_201_CREATED)


class CaptureLinkDetailView(generics.RetrieveAPIView):
    """
    GET /api/capture-link/<uuid>/
    Called on capture page load to validate the UUID and fetch
    customer name + phone for ImageCaptureFlow props.
    Returns 410 if the link has expired.
    """
    queryset         = CaptureLink.objects.all()
    serializer_class = CaptureLinkDetailSerializer
    lookup_field     = "uuid"

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()

        # Auto-expire if past expiry date
        if instance.expires_at and instance.expires_at < timezone.now():
            if instance.status != CaptureLink.STATUS_EXPIRED:
                instance.status = CaptureLink.STATUS_EXPIRED
                instance.save(update_fields=["status"])
            return Response(
                {"detail": "This capture link has expired."},
                status=status.HTTP_410_GONE,
            )

        serializer = self.get_serializer(instance, context={"request": request})
        payload = serializer.data
        payload["link_full"] = request.build_absolute_uri(instance.link_path)
        return Response(payload)


class CaptureLinkListView(generics.ListAPIView):
    """
    GET /api/capture-links/
    Admin / imgcapture_list.jsx link overview.
    Query param: status=pending|used|expired
    """
    serializer_class = CaptureLinkListSerializer

    def get_queryset(self):
        qs = CaptureLink.objects.select_related("customer").all()
        link_status = self.request.query_params.get("status", "").strip()
        if link_status:
            qs = qs.filter(status=link_status)
        return qs


# ══════════════════════════════════════════════════════════════════════════════
# OTP Views
# ══════════════════════════════════════════════════════════════════════════════

class SendOtpView(APIView):
    """
    POST /api/send-otp/
    phoneverify.jsx → handleSend()

    Request  : { phone, uuid? }
    Response : { detail: "OTP sent successfully." }
    """

    def post(self, request, *args, **kwargs):
        serializer = OtpSendSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone    = serializer.validated_data["phone"]
        raw_uuid = serializer.validated_data.get("uuid")

        # Resolve CaptureLink if uuid provided
        link = None
        if raw_uuid:
            try:
                link = CaptureLink.objects.get(uuid=raw_uuid)
            except CaptureLink.DoesNotExist:
                return Response(
                    {"detail": "Invalid capture link."},
                    status=status.HTTP_404_NOT_FOUND,
                )

        # Invalidate any existing active OTPs for this phone
        OtpRecord.objects.filter(phone=phone, status=OtpRecord.STATUS_SENT).update(
            status=OtpRecord.STATUS_EXPIRED
        )

        otp_code = _generate_otp()
        OtpRecord.objects.create(
            capture_link=link,
            phone=phone,
            otp_code=otp_code,
            status=OtpRecord.STATUS_SENT,
        )

        try:
            _send_whatsapp_otp(phone, otp_code)
        except Exception as exc:
            logger.error("OTP delivery failed for %s: %s", phone, exc)
            return Response(
                {"detail": "Failed to deliver OTP. Please try again."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        return Response({"detail": "OTP sent successfully."}, status=status.HTTP_200_OK)


class VerifyOtpView(APIView):
    """
    POST /api/verify-otp/
    Otp_verification.jsx → verifyOtpWithCode()

    Request  : { phone, otp_code, uuid? }
    Response :
        200  { detail: "OTP verified successfully." }
        400  { detail: "Invalid OTP. N attempt(s) remaining." }
        410  { detail: "OTP has expired..." }
        429  { detail: "Too many failed attempts..." }
    """

    def post(self, request, *args, **kwargs):
        serializer = OtpVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone    = serializer.validated_data["phone"]
        otp_code = serializer.validated_data["otp_code"]

        record = (
            OtpRecord.objects
            .filter(phone=phone, status=OtpRecord.STATUS_SENT)
            .order_by("-created_at")
            .first()
        )

        if not record:
            return Response(
                {"detail": "No active OTP found. Please request a new one."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check expiry
        if timezone.now() - record.created_at > timedelta(minutes=OTP_EXPIRY_MINUTES):
            record.status = OtpRecord.STATUS_EXPIRED
            record.save(update_fields=["status"])
            return Response(
                {"detail": "OTP has expired. Please request a new one."},
                status=status.HTTP_410_GONE,
            )

        # Increment attempt counter before checking code
        record.attempts += 1

        if record.attempts >= OTP_MAX_ATTEMPTS:
            record.status = OtpRecord.STATUS_FAILED
            record.save(update_fields=["attempts", "status"])
            return Response(
                {"detail": "Too many failed attempts. Please request a new OTP."},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        if record.otp_code != otp_code:
            record.save(update_fields=["attempts"])
            remaining = OTP_MAX_ATTEMPTS - record.attempts
            return Response(
                {"detail": f"Invalid OTP. {remaining} attempt(s) remaining."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ✓ Verified
        record.status      = OtpRecord.STATUS_VERIFIED
        record.verified_at = timezone.now()
        record.save(update_fields=["status", "verified_at", "attempts"])
        return Response({"detail": "OTP verified successfully."}, status=status.HTTP_200_OK)


class ResendOtpView(APIView):
    """
    POST /api/resend-otp/
    Otp_verification.jsx → resendOtp()
    Internally reuses the same send logic.
    """

    def post(self, request, *args, **kwargs):
        return SendOtpView().post(request, *args, **kwargs)


# ══════════════════════════════════════════════════════════════════════════════
# Image Capture Views
# ══════════════════════════════════════════════════════════════════════════════

class UploadImageView(generics.CreateAPIView):
    """
    POST /api/upload-image/   (multipart/form-data)
    Image_add.jsx → handleUpload()

    Form fields: image (file), uuid, latitude, longitude,
                 address, customer_name, phone
    Returns the verify_success.jsx data shape on success.
    """
    parser_classes   = [MultiPartParser, FormParser]
    serializer_class = ImageCaptureUploadSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        capture = serializer.save()

        # Shape matches verify_success.jsx destructured state
        return Response(
            {
                "id":            capture.id,
                "customerName":  capture.customer_name,
                "phone":         capture.phone,
                "preview":       request.build_absolute_uri(capture.image.url),
                "address":       capture.address,
                "lat":           str(capture.latitude)  if capture.latitude  else None,
                "lng":           str(capture.longitude) if capture.longitude else None,
                "verifiedAt":    capture.verified_at.isoformat(),
                "status":        capture.verification_status,
            },
            status=status.HTTP_201_CREATED,
        )


class ImageCaptureListView(generics.ListAPIView):
    """
    GET /api/captures/
    Powers the imgcapture_list.jsx table.
    Query params: status, manual_status, search
    """
    serializer_class = ImageCaptureListSerializer

    def get_queryset(self):
        qs      = ImageCapture.objects.select_related("capture_link__customer").all()
        vstatus = self.request.query_params.get("status",        "").strip()
        mstatus = self.request.query_params.get("manual_status", "").strip()
        search  = self.request.query_params.get("search",        "").strip()

        if vstatus:
            qs = qs.filter(verification_status=vstatus)
        if mstatus:
            qs = qs.filter(manual_status=mstatus)
        if search:
            qs = qs.filter(customer_name__icontains=search)
        return qs


class ImageCaptureDetailView(generics.RetrieveAPIView):
    """
    GET /api/captures/<pk>/
    Full record — mirrors verify_success.jsx data: customerName,
    phone, preview (image URL), address, lat, lng, verifiedAt.
    """
    queryset         = ImageCapture.objects.all()
    serializer_class = ImageCaptureDetailSerializer


class ManualStatusUpdateView(generics.UpdateAPIView):
    """
    PATCH /api/captures/<pk>/manual-status/
    imgcapture_list.jsx staff action — approve / reject / review.

    Body: { "manual_status": "approved" | "under_review" | "rejected" | "pending" }
    """
    queryset          = ImageCapture.objects.all()
    serializer_class  = ManualStatusUpdateSerializer
    http_method_names = ["patch"]