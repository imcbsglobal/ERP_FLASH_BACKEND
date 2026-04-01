from django.db import models


class Payment(models.Model):

    COLLECTION_TYPE_CHOICES = [
        ('Cash', 'Cash'),
        ('Cheque', 'Cheque'),
        ('Bank Transfer', 'Bank Transfer'),
        ('Credit Card', 'Credit Card'),
        ('Debit Card', 'Debit Card'),
        ('Online Payment', 'Online Payment'),
    ]

    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Completed', 'Completed'),
        ('Failed', 'Failed'),
    ]

    client_name     = models.CharField(max_length=255)
    branch          = models.CharField(max_length=255)
    collection_type = models.CharField(max_length=50, choices=COLLECTION_TYPE_CHOICES)
    amount          = models.DecimalField(max_digits=12, decimal_places=2)
    paid_for        = models.CharField(max_length=255)
    notes           = models.TextField(blank=True, default='')
    payment_proof   = models.FileField(upload_to='payment_proofs/', blank=True, null=True)
    status          = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    date            = models.DateField(auto_now_add=True)
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Payment'
        verbose_name_plural = 'Payments'

    def __str__(self):
        return f"{self.client_name} — ₹{self.amount} ({self.collection_type})"