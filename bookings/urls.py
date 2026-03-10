from django.urls import path
from . import views

app_name = 'bookings'

urlpatterns = [
    # Main pages
    path('', views.index, name='index'),
    path('<str:brand>/book-now/', views.book_now, name='book_now_brand'),
    path('book-now/', views.book_now, name='book_now'),
    
    # Booking submissions
    path('api/offsite-booking/', views.offsite_booking_submit, name='offsite_booking_submit'),
    path('api/onsite-booking/', views.onsite_booking_initiate, name='onsite_booking_initiate'),
    
    # Payment callbacks
    path('success/', views.payment_success, name='payment_success'),
    path('api/cashfree-webhook/', views.cashfree_webhook, name='cashfree_webhook'),
    
    # AJAX endpoints for availability check
    path('api/check-offsite-availability/', views.check_offsite_availability, name='check_offsite_availability'),
    path('api/check-onsite-availability/', views.check_onsite_availability, name='check_onsite_availability'),
    path('shipping-policy/', views.shipping_policy, name='shipping_policy'),
    path('terms-conditions/', views.terms_conditions, name='terms_conditions'),
    path('privacy-policy/', views.privacy_policy, name='privacy_policy'),
    path('refund-returns/', views.refund_returns, name='refund_returns'),
    path('cancellation-policy/', views.cancellation_policy, name='cancellation_policy'),
]