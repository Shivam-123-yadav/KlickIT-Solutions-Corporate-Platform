from django.db import models
from django.utils import timezone

class OnsiteVisitService(models.Model):
    """Onsite service bookings with payment"""
    
    # Device Information
    device_service = models.CharField(max_length=100, verbose_name="Device Name")
    device_problem = models.CharField(max_length=255, verbose_name="Device Problem")
    brand_name = models.CharField(max_length=100)
    model_name = models.CharField(max_length=100, null=True, blank=True)
    serial_number = models.CharField(max_length=100, null=True, blank=True)
    write_issue = models.TextField(verbose_name="Issue Description")
    
    # Customer Information
    customer_name = models.CharField(max_length=200)
    customer_email = models.EmailField()
    customer_mobile = models.CharField(max_length=15)
    mobile_no = models.CharField(max_length=15)  # Duplicate field for compatibility
    customer_address = models.TextField()
    
    # Service Details
    service_center_name = models.CharField(max_length=100)
    service_type = models.CharField(max_length=100)
    booking_date = models.DateField()
    select_time_slot = models.CharField(max_length=50)
    
    # Pricing
    pickup_drop_charges = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    laptop_diagnostic_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_charges = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Payment Information
    order_id = models.CharField(max_length=100, unique=True, null=True, blank=True)
    payment_status = models.CharField(max_length=20, default='PENDING')  # PENDING, SUCCESS, FAILED
    transaction_id = models.CharField(max_length=100, null=True, blank=True)
    payment_method = models.CharField(max_length=50, null=True, blank=True)
    payment_time = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    website_url = models.URLField(default='https://klickit.co.in')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'onsite_visit_service'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['order_id']),
            models.Index(fields=['payment_status']),
            models.Index(fields=['booking_date']),
        ]
    
    def __str__(self):
        return f"{self.customer_name} - {self.device_service} - {self.order_id}"


class OffsiteVisitService(models.Model):
    """Offsite/Walk-in service bookings (no payment required)"""
    
    # Device Information
    device_service = models.CharField(max_length=100, verbose_name="Device Name")
    device_problem = models.CharField(max_length=255, verbose_name="Device Problem")
    brand_name = models.CharField(max_length=100)
    model_name = models.CharField(max_length=100, null=True, blank=True)
    serial_number = models.CharField(max_length=100, null=True, blank=True)
    write_issue = models.TextField(verbose_name="Issue Description")
    
    # Customer Information
    customer_name = models.CharField(max_length=200)
    customer_email = models.EmailField()
    customer_mobile = models.CharField(max_length=15)
    mobile_no = models.CharField(max_length=15)
    customer_address = models.TextField()
    
    # Service Details
    service_center_name = models.CharField(max_length=100)
    service_type = models.CharField(max_length=100)
    booking_date = models.DateField()
    select_time_slot = models.CharField(max_length=50)
    
    # Metadata
    website_url = models.URLField(default='https://klickit.co.in')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'offsite_visit_service'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['booking_date']),
            models.Index(fields=['customer_email']),
        ]
    
    def __str__(self):
        return f"{self.customer_name} - {self.device_service}"


class CashfreePayment(models.Model):
    """Track Cashfree payment transactions"""
    
    order_id = models.CharField(max_length=100, unique=True)
    order_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Customer details
    customer_id = models.CharField(max_length=100)
    customer_name = models.CharField(max_length=200)
    customer_email = models.EmailField()
    customer_phone = models.CharField(max_length=15)
    
    # Cashfree response
    cf_order_id = models.CharField(max_length=100, null=True, blank=True)
    transaction_id = models.CharField(max_length=100, null=True, blank=True)
    payment_session_id = models.CharField(max_length=200, null=True, blank=True)
    payment_status = models.CharField(max_length=20, default='PENDING')
    payment_time = models.DateTimeField(null=True, blank=True)
    callback_response = models.JSONField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'cashfree_payment'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['order_id']),
            models.Index(fields=['cf_order_id']),
        ]
    
    def __str__(self):
        return f"{self.order_id} - {self.payment_status}"


class Holiday(models.Model):
    """Store holiday dates to block bookings"""
    
    date = models.DateField(unique=True)
    name = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    
    class Meta:
        db_table = 'holidays'
        ordering = ['date']
    
    def __str__(self):
        return f"{self.date} - {self.name}"