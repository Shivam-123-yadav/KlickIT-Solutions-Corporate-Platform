from django.shortcuts import render

# Create your views here.
import json
import requests
import uuid
from datetime import datetime, date, timedelta
from django.shortcuts import render, redirect
import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db.models import Count, Q
from django.conf import settings
from django.utils import timezone
from django.db import DataError

from .models import OnsiteVisitService, OffsiteVisitService, CashfreePayment, Holiday
from .forms import OnsiteBookingForm, OffsiteBookingForm
from .utils import (
    generate_pdf_report, 
    send_booking_email, 
    send_whatsapp_message,
    get_brand_logo_url,
    get_brand_link,
    extract_payment_method_type
)


# ==================== HOME PAGE ====================
def index(request):
    """Main landing page"""
    return render(request, 'bookings/index.html')


# ==================== BOOK NOW PAGE ====================
def book_now(request, brand=None):
    """Book now page with form"""
    context = {}
    if brand:
        context['preselected_brand'] = brand.lower()
    return render(request, 'bookings/book_now.html', context)

def shipping_policy(request):
    return render(request, 'shipping_policy.html')  # template ka path adjust kar lena


def terms_conditions(request):
    return render(request, 'terms_conditions.html')  # template ka path adjust kar lena


def privacy_policy(request):
    return render(request, 'privacy_policy.html')  # ya jo bhi path tune rakha hai


def refund_returns(request):
    return render(request, 'refund_returns.html')  # path adjust kar lena

def cancellation_policy(request):
    return render(request, 'cancellation_policy.html')  # path adjust kar lena
# ==================== OFFSITE BOOKING (Walk-in) ====================
@csrf_exempt
@require_http_methods(["POST"])
def offsite_booking_submit(request):
    """Handle offsite booking submission (no payment required)"""
    logger = logging.getLogger(__name__)

    form = OffsiteBookingForm(request.POST)

    if not form.is_valid():
        # Log POST data and form errors for debugging
        try:
            post_data = dict(request.POST)
        except Exception:
            post_data = str(request.POST)

        logger.error('Offsite booking validation failed. POST data: %s', post_data)
        logger.error('Offsite booking form errors: %s', form.errors.as_json())

        return JsonResponse({
            'status': 'error',
            'message': 'Form validation failed',
            'errors': form.errors.get_json_data()
        }, status=400)
    
    # Create booking
    try:
        booking = OffsiteVisitService.objects.create(
            device_service=form.cleaned_data['device_name'],
            device_problem=form.cleaned_data['device_problems'],
            brand_name=form.cleaned_data['brand_name'],
            model_name=form.cleaned_data['model_name'],
            serial_number=form.cleaned_data.get('serial_number', ''),
            write_issue=form.cleaned_data['write_issue'],
            customer_name=form.cleaned_data['customer_name'],
            customer_email=form.cleaned_data['customer_email'],
            customer_mobile=form.cleaned_data['customer_mobile_number'],
            mobile_no=form.cleaned_data['customer_mobile_number'],
            customer_address=form.cleaned_data['customer_address_home'],
            service_center_name=form.cleaned_data['selected_slotservice'],
            service_type=form.cleaned_data['service_types'],
            booking_date=form.cleaned_data['booking_date'],
            select_time_slot=form.cleaned_data['time_slots'],
            website_url=form.cleaned_data.get('website_url', 'https://klickit.co.in')
        )
        
        # Generate PDF
        pdf_path = generate_pdf_report(booking, booking_type='offsite')
        
        # Send email
        send_booking_email(booking, pdf_path, booking_type='offsite')
        
        # Send WhatsApp to customer
        customer_message = f"Hello {booking.customer_name}, your offsite service booking has been confirmed! Booking Date: {booking.booking_date}, Time: {booking.select_time_slot}"
        send_whatsapp_message(booking.customer_mobile, customer_message, pdf_path)
        
        # Send WhatsApp to admin
        admin_message = f"New offsite booking from {booking.customer_name}. Device: {booking.device_service}, Problem: {booking.device_problem}"
        admin_numbers = ['9137445519', '9199137445519']
        for admin in admin_numbers:
            send_whatsapp_message(admin, admin_message, pdf_path)
        
        return JsonResponse({
            'status': 'success',
            'message': 'Your service has been submitted successfully! Confirmation sent to your email and WhatsApp.'
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Booking failed: {str(e)}'
        }, status=500)


# ==================== ONSITE BOOKING (Payment Required) ====================
@csrf_exempt
@require_http_methods(["POST"])
def onsite_booking_initiate(request):
    """Initiate onsite booking and redirect to payment"""
    logger = logging.getLogger(__name__)
    
    form = OnsiteBookingForm(request.POST)
    
    if not form.is_valid():
        logger.error('Onsite booking validation failed. POST data: %s', dict(request.POST))
        logger.error('Form errors: %s', form.errors.as_json())
        return JsonResponse({
            'status': 'error',
            'message': 'Form validation failed',
            'errors': form.errors.get_json_data()
        }, status=400)
    
    # Extract form data
    data = form.cleaned_data
    
    # Generate unique order ID (Cashfree requires alphanumeric, max 36 chars)
    order_id = f"ORD_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8].upper()}"
    
    # Cashfree credentials from settings
    API_KEY = settings.CASHFREE_API_KEY
    SECRET_KEY = settings.CASHFREE_SECRET_KEY
    API_URL = settings.CASHFREE_API_URL
    
    # Prepare Cashfree order payload
    cashfree_payload = {
        "order_id": order_id,
        "order_amount": float(data['total_charges']),
        "order_currency": "INR",
        "customer_details": {
            "customer_id": data['customer_mobile_number'],
            "customer_name": data['customer_name'],
            "customer_email": data['customer_email'],
            "customer_phone": data['customer_mobile_number']
        },
        "order_meta": {
            "return_url": f"{settings.SITE_URL}/success/?order_id={order_id}"
        }
    }
    
    # Make API request to Cashfree
    headers = {
        "Content-Type": "application/json",
        "x-client-id": API_KEY,
        "x-client-secret": SECRET_KEY,
        "x-api-version": "2022-01-01"
    }
    
    try:
        logger.info('Sending Cashfree payload: %s', cashfree_payload)
        response = requests.post(API_URL, json=cashfree_payload, headers=headers, timeout=10)
        logger.info('Cashfree response status: %s', response.status_code)
        logger.info('Cashfree response body: %s', response.text)
        response.raise_for_status()
        result = response.json()
        logger.info('Cashfree result: %s', result)
        
        if 'cf_order_id' in result:
            cf_order_id = result['cf_order_id']
            payment_session_id = result.get('payment_session_id') or result.get('order_token')
            
            # Save payment record
            CashfreePayment.objects.create(
                order_id=order_id,
                order_amount=data['total_charges'],
                customer_id=data['customer_mobile_number'],
                customer_name=data['customer_name'],
                customer_email=data['customer_email'],
                customer_phone=data['customer_mobile_number'],
                cf_order_id=cf_order_id,
                payment_session_id=payment_session_id,
                payment_status='PENDING',
                payment_time=timezone.now(),
                callback_response=result
            )
            
            # Save booking with PENDING status
            OnsiteVisitService.objects.create(
                device_service=data['device_name'],
                device_problem=data['device_problems'],
                brand_name=data['brand_name'],
                model_name=data['model_name'],
                serial_number=data.get('serial_number', ''),
                write_issue=data['write_issue'],
                customer_name=data['customer_name'],
                customer_email=data['customer_email'],
                customer_mobile=data['customer_mobile_number'],
                mobile_no=data['customer_mobile_number'],
                customer_address=data['customer_address_home'],
                service_center_name=data['selected_slotservice'],
                service_type=data['service_types'],
                booking_date=data['booking_date'],
                select_time_slot=data['time_slots'],
                pickup_drop_charges=data['pick_up_drop_charge'],
                laptop_diagnostic_charge=data['diagnostic_charges'],
                total_charges=data['total_charges'],
                order_id=order_id,
                payment_status='PENDING',
                website_url=data.get('website_url', 'https://klickit.co.in')
            )
            
            # Redirect to payment page
            payment_link = result.get('payment_link') or f"https://sandbox.cashfree.com/pg/view/sessions/checkout/web/{payment_session_id}"
            
            return JsonResponse({
                'status': 'success',
                'payment_link': payment_link
            })
        
        else:
            return JsonResponse({
                'status': 'error',
                'message': 'Cashfree API error',
                'details': result
            }, status=500)
            
    except requests.exceptions.RequestException as e:
        error_details = f'{str(e)}'
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_details += f' | Response: {e.response.text}'
            except:
                pass
        logger.error('Cashfree API error: %s', error_details)
        return JsonResponse({
            'status': 'error',
            'message': f'Payment gateway error: {str(e)}'
        }, status=500)
    except Exception as e:
        logger.error('Unexpected error in onsite booking: %s', str(e), exc_info=True)
        return JsonResponse({
            'status': 'error',
            'message': f'Unexpected error: {str(e)}'
        }, status=500)


# ==================== PAYMENT SUCCESS CALLBACK ====================
def payment_success(request):
    """Handle payment success callback from Cashfree"""
    logger = logging.getLogger(__name__)
    
    order_id = request.GET.get('order_id')
    
    if not order_id:
        logger.error('payment_success: Missing order_id in request')
        return render(request, 'bookings/payment_error.html', {
            'message': 'Invalid order ID'
        })
    
    try:
        logger.info(f'payment_success: Processing order_id={order_id}')
        
        # Get booking
        booking = OnsiteVisitService.objects.get(order_id=order_id)
        payment = CashfreePayment.objects.get(order_id=order_id)
        
        logger.info(f'payment_success: Found booking and payment for {order_id}')
        
        # Verify payment status with Cashfree API
        API_KEY = settings.CASHFREE_API_KEY
        SECRET_KEY = settings.CASHFREE_SECRET_KEY
        
        # Fix the URL construction - remove '/orders' only if it exists
        base_url = settings.CASHFREE_API_URL.replace('/orders', '')
        # Use the merchant order_id (ORD_...) for verification, not the numeric cf_order_id
        verify_url = f"{base_url}/orders/{payment.order_id}"
        
        logger.info(f'payment_success: Verifying payment with URL: {verify_url}')
        
        headers = {
            "x-client-id": API_KEY,
            "x-client-secret": SECRET_KEY,
            "x-api-version": "2022-01-01"
        }
        
        response = requests.get(verify_url, headers=headers, timeout=10)
        response.raise_for_status()
        result = response.json()
        
        logger.info(f'payment_success: Cashfree API response: {result}')
        
        # Cashfree returns order_status with values like PAID, FAILED, EXPIRED, CANCELLED
        payment_status = result.get('order_status', 'PENDING')
        
        logger.info(f'payment_success: Payment status for {order_id}: {payment_status}')
        
        if payment_status == 'PAID':
            logger.info(f'payment_success: Payment PAID for {order_id}, updating booking')

            # Attempt to extract payment/transaction id. Cashfree may not include cf_payment_id
            # in the order response; in that case call the payments endpoint to get details.
            payment_id = result.get('cf_payment_id') or result.get('payment_id')
            payment_method = extract_payment_method_type(result.get('payment_method'))

            if not payment_id:
                # Try to fetch payments list from the order payments URL
                payments_url = None
                payments_obj = result.get('payments')
                # payments can be dict, list, or string; handle safely
                if isinstance(payments_obj, dict):
                    payments_url = payments_obj.get('url')
                elif isinstance(payments_obj, str):
                    payments_url = payments_obj
                else:
                    payments_url = None

                if not payments_url:
                    # Construct a fallback payments URL
                    payments_url = f"{base_url}/orders/{payment.order_id}/payments"

                try:
                    logger.info(f'payment_success: Fetching payments from {payments_url}')
                    pay_resp = requests.get(payments_url, headers=headers, timeout=10)
                    pay_resp.raise_for_status()
                    pay_data = pay_resp.json()

                    # pay_data may be a list (direct list of payments) or a dict
                    payments_list = None
                    if isinstance(pay_data, list):
                        payments_list = pay_data
                    elif isinstance(pay_data, dict):
                        payments_list = (
                            pay_data.get('items') or pay_data.get('payments') or
                            pay_data.get('data') or pay_data.get('result')
                        )
                        # If payments_list is not a list, try to find the first list value inside the dict
                        if not isinstance(payments_list, list):
                            for v in pay_data.values():
                                if isinstance(v, list):
                                    payments_list = v
                                    break

                    found_id = None
                    found_method = None
                    if isinstance(payments_list, list) and len(payments_list) > 0:
                        # iterate payments to find a sensible payment id
                        for p in payments_list:
                            if not isinstance(p, dict):
                                continue
                            # common keys that might contain the payment/transaction id
                            candidates = [
                                'cf_payment_id', 'payment_id', 'paymentId', 'id', 'reference_id', 'txnid', 'transaction_id', 'payment_reference'
                            ]
                            for key in candidates:
                                if key in p and p.get(key):
                                    found_id = p.get(key)
                                    break
                            # also check nested 'payment' or 'transaction' objects
                            if not found_id:
                                for nested_key in ['payment', 'transaction']:
                                    nested = p.get(nested_key)
                                    if isinstance(nested, dict):
                                        for key in candidates:
                                            if key in nested and nested.get(key):
                                                found_id = nested.get(key)
                                                break
                                        if found_id:
                                            break
                            # find payment method
                            if not found_method:
                                found_method = p.get('payment_method') or p.get('mode') or p.get('method')
                            if found_id:
                                # prefer first found non-empty id
                                payment_id = found_id
                                payment_method = payment_method or extract_payment_method_type(found_method)
                                break
                        # attach payments list to callback for debugging/audit
                        result['payments_list'] = payments_list
                    else:
                        logger.info('payment_success: No payments list found in payments endpoint response')
                except Exception as e:
                    logger.warning(f'payment_success: Could not fetch payments list: {str(e)}')

            # Helper to safely truncate fields to DB column sizes
            def _safe_truncate(val, maxlen):
                try:
                    if val is None:
                        return ''
                    s = str(val)
                    return s[:maxlen]
                except Exception:
                    return ''

            # Update booking status
            booking.payment_status = 'SUCCESS'
            booking.transaction_id = _safe_truncate(payment_id or '', 100)
            booking.payment_method = _safe_truncate(payment_method or 'Online', 50)
            booking.payment_time = timezone.now()
            try:
                booking.save()
            except DataError:
                # Fallback: aggressively truncate and retry
                booking.transaction_id = _safe_truncate(booking.transaction_id, 100)
                booking.payment_method = _safe_truncate(booking.payment_method, 50)
                booking.save()
            
            # Update payment record
            payment.payment_status = 'SUCCESS'
            # save transaction id to payment record as well for reliable storage
            if payment_id:
                try:
                    payment.transaction_id = _safe_truncate(payment_id, 100)
                except Exception:
                    payment.transaction_id = payment.transaction_id or None
            payment.callback_response = result
            payment.save()
            
            # Generate PDF
            pdf_path = generate_pdf_report(booking, booking_type='onsite')
            
            # Send email
            send_booking_email(booking, pdf_path, booking_type='onsite')
            
            # Send WhatsApp to customer
            customer_message = f"Hello {booking.customer_name}, your payment of ₹{booking.total_charges} is successful! Your pickup is scheduled for {booking.booking_date} at {booking.select_time_slot}"
            send_whatsapp_message(booking.customer_mobile, customer_message, pdf_path)
            
            # Send WhatsApp to admin
            admin_message = f"New paid booking from {booking.customer_name}. Amount: ₹{booking.total_charges}, Device: {booking.device_service}"
            admin_numbers = ['9137445519', '9199137445519']
            for admin in admin_numbers:
                send_whatsapp_message(admin, admin_message, pdf_path)
            
            # Compute a display transaction id: prefer booking.transaction_id,
            # otherwise try to extract from saved payment.callback_response
            display_tid = booking.transaction_id
            if not display_tid:
                try:
                    cb = payment.callback_response or {}
                    display_tid = (
                        cb.get('cf_payment_id') or cb.get('payment_id') or cb.get('transaction_id')
                        or cb.get('txnid') or cb.get('reference_id')
                    )

                    if not display_tid:
                        payments_list = (
                            cb.get('payments') or cb.get('data') or cb.get('items') or cb.get('result')
                        )
                        # normalize to list if nested
                        if isinstance(payments_list, dict):
                            for v in payments_list.values():
                                if isinstance(v, list):
                                    payments_list = v
                                    break

                        if isinstance(payments_list, list) and len(payments_list) > 0:
                            for p in payments_list:
                                if not isinstance(p, dict):
                                    continue
                                for key in ['cf_payment_id', 'payment_id', 'paymentId', 'id', 'reference_id', 'txnid', 'transaction_id', 'payment_reference']:
                                    if p.get(key):
                                        display_tid = p.get(key)
                                        break
                                if display_tid:
                                    break
                except Exception:
                    display_tid = display_tid or ''

            if not display_tid:
                display_tid = 'N/A'

            # Format payment method for display on success page
            try:
                from .utils import format_payment_method
                payment_method_display = format_payment_method(getattr(booking, 'payment_method', None))
            except Exception:
                payment_method_display = getattr(booking, 'payment_method', '') or 'N/A'

            return render(request, 'bookings/payment_success.html', {
                'booking': booking,
                'transaction_id': display_tid,
                'payment_method': payment_method_display,
            })
        
        else:
            # Payment failed, cancelled, or expired
            logger.warning(f'payment_success: Payment not successful - status: {payment_status}')
            
            booking.payment_status = 'FAILED'
            booking.save()
            
            payment.payment_status = payment_status
            payment.callback_response = result
            payment.save()
            
            # Determine error message based on status
            error_messages = {
                'CANCELLED': 'Payment was cancelled by you.',
                'FAILED': 'Payment failed. Please try again.',
                'EXPIRED': 'Payment link has expired. Please try again.',
                'PENDING': 'Payment is still pending. Please try again.'
            }
            
            message = error_messages.get(payment_status, f'Payment failed with status: {payment_status}')
            
            return render(request, 'bookings/payment_error.html', {
                'message': message,
                'order_id': order_id
            })
        
    except (OnsiteVisitService.DoesNotExist, CashfreePayment.DoesNotExist) as e:
        logger.error(f'payment_success: Booking or payment not found for {order_id}: {str(e)}')
        return render(request, 'bookings/payment_error.html', {
            'message': 'Booking not found'
        })
    except requests.exceptions.RequestException as e:
        logger.error(f'payment_success: Cashfree API request failed: {str(e)}', exc_info=True)
        return render(request, 'bookings/payment_error.html', {
            'message': f'Unable to verify payment status. Please contact support with order ID: {order_id}'
        })
    except Exception as e:
        logger.error(f'payment_success: Unexpected error for {order_id}: {str(e)}', exc_info=True)
        return render(request, 'bookings/payment_error.html', {
            'message': f'Error: {str(e)}'
        })


# ==================== CHECK BOOKING AVAILABILITY (AJAX) ====================
@csrf_exempt
@require_http_methods(["GET"])
def check_offsite_availability(request):
    """Check available time slots for offsite bookings"""
    
    selected_date = request.GET.get('date')
    
    if not selected_date:
        return JsonResponse({'success': False, 'message': 'Date required'})
    
    try:
        # Get bookings for selected date grouped by time slot and service center
        bookings = OffsiteVisitService.objects.filter(
            booking_date=selected_date
        ).values(
            'select_time_slot', 
            'service_center_name'
        ).annotate(count=Count('id'))
        
        # Format response
        dates = [
            {
                'date': selected_date,
                'time_slot': booking['select_time_slot'],
                'service_center': booking['service_center_name'],
                'count': booking['count']
            }
            for booking in bookings
        ]
        
        return JsonResponse({'success': True, 'dates': dates})
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@csrf_exempt
@require_http_methods(["GET"])
def check_onsite_availability(request):
    """Check available time slots for onsite bookings"""
    
    selected_date = request.GET.get('date')
    
    if not selected_date:
        return JsonResponse({'success': False, 'message': 'Date required'})
    
    try:
        # Get bookings for selected date grouped by time slot and service center (only successful or pending payments)
        bookings = OnsiteVisitService.objects.filter(
            booking_date=selected_date,
            payment_status__in=['PENDING', 'SUCCESS']
        ).values(
            'select_time_slot', 
            'service_center_name'
        ).annotate(count=Count('id'))
        
        # Format response
        dates = [
            {
                'date': selected_date,
                'time_slot': booking['select_time_slot'],
                'service_center': booking['service_center_name'],
                'count': booking['count']
            }
            for booking in bookings
        ]
        
        return JsonResponse({'success': True, 'dates': dates})
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


# ==================== WEBHOOK FOR CASHFREE ====================
@csrf_exempt
@require_http_methods(["POST"])
def cashfree_webhook(request):
    """Handle Cashfree payment webhook notifications"""
    
    try:
        payload = json.loads(request.body)
        
        order_id = payload.get('order_id')
        payment_status = payload.get('payment_status')
        
        if not order_id:
            return JsonResponse({'status': 'error', 'message': 'Missing order_id'})
        
        # Update payment record
        payment = CashfreePayment.objects.get(order_id=order_id)
        payment.payment_status = payment_status
        # store transaction id if provided in webhook
        txid = payload.get('cf_payment_id') or payload.get('payment_id') or payload.get('transaction_id')
        if not txid:
            tx = payload.get('payment')
            if isinstance(tx, dict):
                txid = tx.get('cf_payment_id') or tx.get('payment_id') or tx.get('transaction_id')
        if txid:
            payment.transaction_id = str(txid)[:100]
        payment.callback_response = payload
        payment.save()
        
        # Update booking
        booking = OnsiteVisitService.objects.get(order_id=order_id)
        
        if payment_status == 'SUCCESS':
            # truncate to model limits
            def _safe_truncate(val, maxlen):
                try:
                    if val is None:
                        return ''
                    return str(val)[:maxlen]
                except Exception:
                    return ''

            booking.payment_status = 'SUCCESS'
            booking.transaction_id = _safe_truncate(payload.get('cf_payment_id') or payload.get('payment_id') or payload.get('transaction_id'), 100)
            booking.payment_method = _safe_truncate(extract_payment_method_type(payload.get('payment_method')) or 'Online', 50)
            booking.payment_time = timezone.now()
            booking.save()
            
            # Send notifications
            pdf_path = generate_pdf_report(booking, booking_type='onsite')
            send_booking_email(booking, pdf_path, booking_type='onsite')
            
            customer_message = f"Payment successful! ₹{booking.total_charges} received."
            send_whatsapp_message(booking.customer_mobile, customer_message, pdf_path)
        
        return JsonResponse({'status': 'success'})
        
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})
    

