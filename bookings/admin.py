from django.contrib import admin
from django.utils.html import format_html
from .models import OnsiteVisitService, OffsiteVisitService, CashfreePayment, Holiday


@admin.register(OnsiteVisitService)
class OnsiteVisitServiceAdmin(admin.ModelAdmin):
    """Admin panel for Onsite bookings with payment"""
    
    list_display = [
        'id', 
        'order_id', 
        'customer_name', 
        'customer_mobile',
        'device_service',
        'brand_name',
        'service_center_name',
        'booking_date',
        'payment_status_badge',
        'total_charges',
        'created_at'
    ]
    
    list_filter = [
        'payment_status',
        'service_center_name',
        'brand_name',
        'booking_date',
        'created_at'
    ]
    
    search_fields = [
        'customer_name',
        'customer_email',
        'customer_mobile',
        'order_id',
        'transaction_id',
        'device_service',
        'brand_name'
    ]
    
    readonly_fields = [
        'order_id',
        'transaction_id',
        'payment_time',
        'created_at',
        'updated_at'
    ]
    
    fieldsets = (
        ('Customer Information', {
            'fields': (
                'customer_name',
                'customer_email',
                'customer_mobile',
                'customer_address'
            )
        }),
        ('Device Information', {
            'fields': (
                'device_service',
                'brand_name',
                'model_name',
                'serial_number',
                'device_problem',
                'write_issue'
            )
        }),
        ('Service Details', {
            'fields': (
                'service_center_name',
                'service_type',
                'booking_date',
                'select_time_slot'
            )
        }),
        ('Payment Information', {
            'fields': (
                'order_id',
                'payment_status',
                'transaction_id',
                'payment_method',
                'payment_time',
                'pickup_drop_charges',
                'laptop_diagnostic_charge',
                'total_charges'
            )
        }),
        ('Metadata', {
            'fields': (
                'website_url',
                'created_at',
                'updated_at'
            ),
            'classes': ('collapse',)
        }),
    )
    
    date_hierarchy = 'booking_date'
    ordering = ['-created_at']
    
    def payment_status_badge(self, obj):
        """Display payment status with color badge"""
        colors = {
            'PENDING': 'orange',
            'SUCCESS': 'green',
            'FAILED': 'red'
        }
        color = colors.get(obj.payment_status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.payment_status
        )
    payment_status_badge.short_description = 'Payment Status'
    
    actions = ['mark_as_success', 'mark_as_failed']
    
    def mark_as_success(self, request, queryset):
        queryset.update(payment_status='SUCCESS')
    mark_as_success.short_description = "Mark selected as SUCCESS"
    
    def mark_as_failed(self, request, queryset):
        queryset.update(payment_status='FAILED')
    mark_as_failed.short_description = "Mark selected as FAILED"


@admin.register(OffsiteVisitService)
class OffsiteVisitServiceAdmin(admin.ModelAdmin):
    """Admin panel for Offsite/Walk-in bookings"""
    
    list_display = [
        'id',
        'customer_name',
        'customer_mobile',
        'device_service',
        'brand_name',
        'service_center_name',
        'booking_date',
        'select_time_slot',
        'created_at'
    ]
    
    list_filter = [
        'service_center_name',
        'brand_name',
        'booking_date',
        'created_at'
    ]
    
    search_fields = [
        'customer_name',
        'customer_email',
        'customer_mobile',
        'device_service',
        'brand_name'
    ]
    
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Customer Information', {
            'fields': (
                'customer_name',
                'customer_email',
                'customer_mobile',
                'customer_address'
            )
        }),
        ('Device Information', {
            'fields': (
                'device_service',
                'brand_name',
                'model_name',
                'serial_number',
                'device_problem',
                'write_issue'
            )
        }),
        ('Service Details', {
            'fields': (
                'service_center_name',
                'service_type',
                'booking_date',
                'select_time_slot'
            )
        }),
        ('Metadata', {
            'fields': (
                'website_url',
                'created_at',
                'updated_at'
            ),
            'classes': ('collapse',)
        }),
    )
    
    date_hierarchy = 'booking_date'
    ordering = ['-created_at']


@admin.register(CashfreePayment)
class CashfreePaymentAdmin(admin.ModelAdmin):
    """Admin panel for Cashfree payment tracking"""
    
    list_display = [
        'id',
        'order_id',
        'customer_name',
        'order_amount',
        'payment_status_badge',
        'payment_time',
        'created_at'
    ]
    
    list_filter = [
        'payment_status',
        'payment_time',
        'created_at'
    ]
    
    search_fields = [
        'order_id',
        'cf_order_id',
        'customer_name',
        'customer_email',
        'customer_phone'
    ]
    
    readonly_fields = [
        'order_id',
        'cf_order_id',
        'payment_session_id',
        'callback_response',
        'created_at',
        'updated_at'
    ]
    
    fieldsets = (
        ('Order Information', {
            'fields': (
                'order_id',
                'order_amount',
                'customer_id',
                'customer_name',
                'customer_email',
                'customer_phone'
            )
        }),
        ('Cashfree Details', {
            'fields': (
                'cf_order_id',
                'payment_session_id',
                'payment_status',
                'payment_time'
            )
        }),
        ('Response Data', {
            'fields': (
                'callback_response',
            ),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': (
                'created_at',
                'updated_at'
            ),
            'classes': ('collapse',)
        }),
    )
    
    date_hierarchy = 'payment_time'
    ordering = ['-created_at']
    
    def payment_status_badge(self, obj):
        """Display payment status with color badge"""
        colors = {
            'PENDING': 'orange',
            'SUCCESS': 'green',
            'FAILED': 'red'
        }
        color = colors.get(obj.payment_status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.payment_status
        )
    payment_status_badge.short_description = 'Payment Status'


@admin.register(Holiday)
class HolidayAdmin(admin.ModelAdmin):
    """Admin panel for managing holidays"""
    
    list_display = ['date', 'name', 'description']
    list_filter = ['date']
    search_fields = ['name', 'description']
    ordering = ['date']
    
    fieldsets = (
        ('Holiday Details', {
            'fields': ('date', 'name', 'description')
        }),
    )


# Customize Admin Site
admin.site.site_header = "KlickIT Booking Admin"
admin.site.site_title = "KlickIT Admin Portal"
admin.site.index_title = "Welcome to KlickIT Booking Administration"