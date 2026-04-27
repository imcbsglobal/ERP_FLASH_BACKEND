"""
imagecapture/urls.py

Include in collection_backend/urls.py with:
    path("image_capture/", include("imagecapture.urls")),

Frontend ↔ Backend URL map
──────────────────────────────────────────────────────────────────
Component               Action              Method  Path
──────────────────────────────────────────────────────────────────
Image_link.jsx          customer dropdown   GET     api/customers/
Image_link.jsx          handleGenerate()    POST    api/generate-link/
imgcapture_list.jsx     link overview       GET     api/capture-links/
ImageCaptureFlow        page load (uuid)    GET     api/capture-link/<uuid>/
phoneverify.jsx         handleSend()        POST    api/send-otp/
Otp_verification.jsx    verifyOtpWithCode() POST    api/verify-otp/
Otp_verification.jsx    resendOtp()         POST    api/resend-otp/
Image_add.jsx           handleUpload()      POST    api/upload-image/
imgcapture_list.jsx     table rows          GET     api/captures/
verify_success.jsx      detail view         GET     api/captures/<pk>/
imgcapture_list.jsx     approve/reject      PATCH   api/captures/<pk>/manual-status/
"""
from django.urls import path
from . import views

urlpatterns = [
    # ── Customers ─────────────────────────────────────────────────
    path(
        "api/customers/",
        views.CustomerListCreateView.as_view(),
        name="imagecapture-customer-list",
    ),
    path(
        "api/customers/<int:pk>/",
        views.CustomerDetailView.as_view(),
        name="imagecapture-customer-detail",
    ),

    # ── Capture Links ──────────────────────────────────────────────
    path(
        "api/generate-link/",
        views.GenerateLinkView.as_view(),
        name="imagecapture-generate-link",
    ),
    path(
        "api/capture-link/<uuid:uuid>/",
        views.CaptureLinkDetailView.as_view(),
        name="imagecapture-link-detail",
    ),
    path(
        "api/capture-links/",
        views.CaptureLinkListView.as_view(),
        name="imagecapture-link-list",
    ),

    # ── OTP ────────────────────────────────────────────────────────
    path(
        "api/send-otp/",
        views.SendOtpView.as_view(),
        name="imagecapture-send-otp",
    ),
    path(
        "api/verify-otp/",
        views.VerifyOtpView.as_view(),
        name="imagecapture-verify-otp",
    ),
    path(
        "api/resend-otp/",
        views.ResendOtpView.as_view(),
        name="imagecapture-resend-otp",
    ),

    # ── Image Captures ─────────────────────────────────────────────
    path(
        "api/upload-image/",
        views.UploadImageView.as_view(),
        name="imagecapture-upload",
    ),
    path(
        "api/captures/",
        views.ImageCaptureListView.as_view(),
        name="imagecapture-list",
    ),
    path(
        "api/captures/<int:pk>/",
        views.ImageCaptureDetailView.as_view(),
        name="imagecapture-detail",
    ),
    path(
        "api/captures/<int:pk>/manual-status/",
        views.ManualStatusUpdateView.as_view(),
        name="imagecapture-manual-status",
    ),
]