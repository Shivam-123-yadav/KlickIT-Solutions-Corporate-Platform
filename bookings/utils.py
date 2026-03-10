import os
import requests
from datetime import datetime
from django.core.mail import EmailMessage, get_connection
from django.template.loader import render_to_string
from django.conf import settings
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.units import inch
import json
import ast

# Brand logo mappings
BRAND_LOGOS = {
    'acer': 'acer-logo.webp',
    'apple': 'apple-logo.webp',
    'asus': 'asus-logo.webp',
    'dell': 'dell-logo.webp',
    'hp': 'hp-logo.webp',
    'lenovo': 'lenovo-logo.webp',
    'bose': 'bose-logo.webp',
}

BRAND_LINKS = {
    'acer': 'https://laptopservicencenter.in/',
    'apple': 'http://appleservicescentre.co.in/',
    'asus': 'http://asusservicecentre.in/',
    'dell': 'http://dellservicescentre.co.in/',
    'hp': 'http://hpservicecentre.co.in/',
    'lenovo': 'http://lenovoservicecentre.co.in/',
    'bose': 'https://klickit.co.in/',
}


def get_brand_logo_url(brand_name):
    """Get brand logo URL from brand name"""
    base_url = 'https://klickit.co.in/images/mail-template-logo/'
    default = base_url + 'klickit-logo.webp'
    
    if not brand_name:
        return default
    
    brand = brand_name.lower().strip()
    
    # Exact match
    if brand in BRAND_LOGOS:
        return base_url + BRAND_LOGOS[brand]
    
    # Substring match
    for key, logo in BRAND_LOGOS.items():
        if key in brand:
            return base_url + logo
    
    return default


def get_brand_link(brand_name):
    """Get brand website link"""
    default = 'https://klickit.co.in/'
    
    if not brand_name:
        return default
    
    brand = brand_name.lower().strip()
    
    if brand in BRAND_LINKS:
        return BRAND_LINKS[brand]
    
    for key, link in BRAND_LINKS.items():
        if key in brand:
            return link
    
    return default


def extract_payment_method_type(payment_method_data):
    """Extract just the payment method type from Cashfree payment_method data.
    
    Returns: Simple string like 'UPI', 'Credit Card', 'Debit Card', etc.
    """
    try:
        pm = payment_method_data
        if not pm:
            return 'Online'

        # If it's a JSON-like string, try to parse
        if isinstance(pm, str):
            pm_str = pm.strip()
            if pm_str.startswith('{') or pm_str.startswith('['):
                try:
                    pm = json.loads(pm_str)
                except Exception:
                    # try parsing Python literal (single-quoted dicts) as a fallback
                    try:
                        pm = ast.literal_eval(pm_str)
                    except Exception:
                        # fallback to raw string - check if it's a known method
                        pm_lower = pm_str.lower()
                        if 'upi' in pm_lower:
                            return 'UPI'
                        elif 'credit' in pm_lower:
                            return 'Credit Card'
                        elif 'debit' in pm_lower:
                            return 'Debit Card'
                        elif 'netbanking' in pm_lower:
                            return 'Net Banking'
                        return pm_str

        # Now handle dict types
        if isinstance(pm, dict):
            # UPI structure: {'upi': {...}}
            if 'upi' in pm:
                return 'UPI'

            # Card structure: {'card': {...}}
            if 'card' in pm:
                card = pm['card']
                if isinstance(card, dict):
                    card_type = card.get('type') or card.get('card_type')
                    if card_type:
                        # Normalize card type
                        card_type_lower = str(card_type).lower()
                        if 'debit' in card_type_lower:
                            return 'Debit Card'
                        elif 'credit' in card_type_lower:
                            return 'Credit Card'
                        return card_type.title()
                return 'Card'

            # Wallet structure
            if 'wallet' in pm:
                return 'Wallet'

            # Net Banking
            if 'netbanking' in pm or 'net_banking' in pm:
                return 'Net Banking'

            # Fallback: if single-key wrapper like {'upi':{...}}
            if len(pm) == 1:
                k = next(iter(pm.keys()))
                k_lower = k.lower()
                if 'upi' in k_lower:
                    return 'UPI'
                elif 'card' in k_lower:
                    return 'Card'
                elif 'wallet' in k_lower:
                    return 'Wallet'
                elif 'netbanking' in k_lower or 'net_banking' in k_lower:
                    return 'Net Banking'
                return k.title()

            # Generic fallback
            return 'Online'

        # Non-dict, non-string values -> convert to string
        return str(pm)
    except Exception:
        return 'Online'


def format_payment_method(payment_method):
    """Format payment method for display.
    
    If payment_method is the complex dict from Cashfree, extracts just the type.
    Otherwise returns it as-is.
    """
    try:
        if not payment_method:
            return 'N/A'
        
        # If already a simple string (like 'UPI', 'Credit Card'), return it
        if isinstance(payment_method, str):
            pm_str = payment_method.strip()
            # Check if it's already a simple payment method type
            simple_methods = ['UPI', 'Credit Card', 'Debit Card', 'Net Banking', 'Wallet', 'Online']
            if pm_str in simple_methods:
                return pm_str
            # Otherwise try to extract from complex structure
            return extract_payment_method_type(payment_method)
        
        # If it's a dict or complex structure, extract the type
        return extract_payment_method_type(payment_method)
    except Exception:
        return 'N/A'


# def generate_pdf_report(booking, booking_type='onsite'):
#     """
#     Generate PDF report for booking
#     Returns: PDF file path
#     """
#     # Create directory if not exists
#     pdf_dir = os.path.join(settings.MEDIA_ROOT, 'pdf_reports')
#     os.makedirs(pdf_dir, exist_ok=True)
    
#     # Generate unique filename
#     safe_name = booking.customer_name.replace(' ', '_')
#     timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
#     pdf_filename = f"{booking_type}_visit_{safe_name}_{timestamp}.pdf"
#     pdf_path = os.path.join(pdf_dir, pdf_filename)
    
#     # Create PDF
#     doc = SimpleDocTemplate(pdf_path, pagesize=A4)
#     elements = []
#     styles = getSampleStyleSheet()
    
#     # Custom styles
#     title_style = ParagraphStyle(
#         'CustomTitle',
#         parent=styles['Heading1'],
#         fontSize=16,
#         textColor=colors.HexColor('#0f0bb3'),
#         alignment=1  # Center
#     )
    
#     heading_style = ParagraphStyle(
#         'CustomHeading',
#         parent=styles['Heading2'],
#         fontSize=12,
#         textColor=colors.HexColor('#d35827'),
#         backColor=colors.HexColor('#f5f5f5'),
#         spaceBefore=10,
#         spaceAfter=5
#     )
    
#     # Title
#     if booking_type == 'onsite':
#         title_text = "Pickup & Delivery Service Confirmation"
#     else:
#         title_text = "Offsite Service Visit Confirmation"
    
#     title = Paragraph(title_text, title_style)
#     elements.append(title)
#     elements.append(Spacer(1, 20))
    
#     # Personal Information
#     elements.append(Paragraph("Personal Information", heading_style))
#     personal_data = [
#         ['Name', booking.customer_name],
#         ['Email', booking.customer_email],
#         ['Mobile Number', booking.customer_mobile],
#         ['Address', booking.customer_address],
#     ]
#     personal_table = Table(personal_data, colWidths=[2*inch, 4*inch])
#     personal_table.setStyle(TableStyle([
#         ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#bcc8f3')),
#         ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
#         ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
#         ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
#         ('FONTSIZE', (0, 0), (-1, -1), 10),
#         ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#c3c8d5')),
#         ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
#     ]))
#     elements.append(personal_table)
#     elements.append(Spacer(1, 15))
    
#     # Device Information
#     elements.append(Paragraph("Device Information", heading_style))
#     device_data = [
#         ['Device Name', booking.device_service],
#         ['Brand Name', booking.brand_name],
#         ['Model Name', booking.model_name or 'N/A'],
#         ['Device Problem', booking.device_problem],
#         ['Issue', booking.write_issue],
#     ]
#     device_table = Table(device_data, colWidths=[2*inch, 4*inch])
#     device_table.setStyle(TableStyle([
#         ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#bcc8f3')),
#         ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
#         ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
#         ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
#         ('FONTSIZE', (0, 0), (-1, -1), 10),
#         ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#c3c8d5')),
#         ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
#     ]))
#     elements.append(device_table)
#     elements.append(Spacer(1, 15))
    
#     # Service Details
#     elements.append(Paragraph("Service Details", heading_style))
#     service_data = [
#         ['Service Center', booking.service_center_name],
#         ['Service Type', booking.service_type],
#         ['Booking Date', str(booking.booking_date)],
#         ['Time Slot', booking.select_time_slot],
#     ]
#     service_table = Table(service_data, colWidths=[2*inch, 4*inch])
#     service_table.setStyle(TableStyle([
#         ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#bcc8f3')),
#         ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
#         ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
#         ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
#         ('FONTSIZE', (0, 0), (-1, -1), 10),
#         ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#c3c8d5')),
#         ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
#     ]))
#     elements.append(service_table)
#     elements.append(Spacer(1, 15))
    
#     # Add pricing for onsite bookings
#     if booking_type == 'onsite' and hasattr(booking, 'total_charges'):
#         elements.append(Paragraph("Service Charges", heading_style))
#         pricing_data = [
#             ['Pickup & Drop Charges', f'₹ {booking.pickup_drop_charges}'],
#             ['Diagnostic Charges', f'₹ {booking.laptop_diagnostic_charge}'],
#             ['Total Charges', f'₹ {booking.total_charges}'],
#         ]
#         pricing_table = Table(pricing_data, colWidths=[2*inch, 4*inch])
#         pricing_table.setStyle(TableStyle([
#             ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#bcc8f3')),
#             ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#2575fc')),
#             ('TEXTCOLOR', (0, 0), (-1, -2), colors.black),
#             ('TEXTCOLOR', (0, -1), (-1, -1), colors.white),
#             ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
#             ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
#             ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
#             ('FONTSIZE', (0, 0), (-1, -1), 10),
#             ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#c3c8d5')),
#             ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
#         ]))
#         elements.append(pricing_table)
#         elements.append(Spacer(1, 15))
        
#         # Transaction details
#         if booking.transaction_id:
#             elements.append(Paragraph("Transaction Details", heading_style))
#             transaction_data = [
#                 ['Transaction ID', booking.transaction_id],
#                 ['Payment Method', format_payment_method(getattr(booking, 'payment_method', None))],
#                 ['Payment Time', str(booking.payment_time) if booking.payment_time else 'N/A'],
#             ]
#             transaction_table = Table(transaction_data, colWidths=[2*inch, 4*inch])
#             transaction_table.setStyle(TableStyle([
#                 ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#bcc8f3')),
#                 ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
#                 ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
#                 ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
#                 ('FONTSIZE', (0, 0), (-1, -1), 10),
#                 ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#c3c8d5')),
#                 ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
#             ]))
#             elements.append(transaction_table)
    
#     # Footer
#     elements.append(Spacer(1, 20))
#     footer_text = """
#     <para align=center>
#     Need help? Contact us on WhatsApp 9987223322<br/>
#     Visit our website: www.klickit.co.in<br/>
#     Thank you for choosing our services!
#     </para>
#     """
#     footer = Paragraph(footer_text, styles['Normal'])
#     elements.append(footer)
    
#     # Build PDF
#     doc.build(elements)
    
#     return pdf_path

# import os
# from django.conf import settings
# from django.template.loader import render_to_string
# from weasyprint import HTML
# from datetime import datetime

# def generate_pdf_report(booking, booking_type='onsite'):
#     pdf_dir = os.path.join(settings.MEDIA_ROOT, 'pdf_reports')
#     os.makedirs(pdf_dir, exist_ok=True)

#     safe_name = booking.customer_name.replace(' ', '_')
#     timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
#     file_name = f"{booking_type}_{safe_name}_{timestamp}.pdf"
#     pdf_path = os.path.join(pdf_dir, file_name)

#     context = {
#         'booking': booking,
#         'logo_url': settings.BASE_DIR / 'static/images/klickit-logo.webp',
#         'side_image_url': settings.BASE_DIR / 'static/images/v1.png',
#     }

#     html = render_to_string('pdf/booking_confirmation.html', context)

#     HTML(string=html, base_url=settings.BASE_DIR).write_pdf(pdf_path)

#     return pdf_path

# import os
# from datetime import datetime
# from django.conf import settings
# from django.template.loader import render_to_string
# from weasyprint import HTML, CSS
# import logging  # For debugging WeasyPrint issues

# logger = logging.getLogger(__name__)

# def generate_pdf_report(booking, booking_type):
#     """
#     booking_type = 'onsite' | 'offsite'
#     """
#     if booking_type not in ['onsite', 'offsite']:
#         raise ValueError("Invalid booking_type")

#     pdf_dir = os.path.join(settings.MEDIA_ROOT, 'pdf_reports')
#     os.makedirs(pdf_dir, exist_ok=True)

#     safe_name = booking.customer_name.replace(' ', '_')
#     timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

#     pdf_filename = f"{booking_type}_visit_{safe_name}_{timestamp}.pdf"
#     pdf_path = os.path.join(pdf_dir, pdf_filename)

#     # TEMPLATE SELECTION
#     template_name = (
#         'pdf/offsite_confirmation.html'
#         if booking_type == 'offsite'
#         else 'pdf/onsite_confirmation.html'
#     )

#     # Use relative paths for images (resolvable via base_url)
#     context = {
#         'booking': booking,
#         'booking_type': booking_type,
#         'logo_url': 'static/images/klickit-logo.webp',  # Relative path
#         'side_image_url': 'static/images/v1.png',       # Relative path
#     }

#     html_string = render_to_string(template_name, context)

#     try:
#         # Generate PDF with base_url for resolving relative paths
#         html_doc = HTML(string=html_string, base_url=str(settings.BASE_DIR))
#         html_doc.write_pdf(pdf_path)
#         logger.info(f"PDF generated successfully: {pdf_path}")
#     except Exception as e:
#         logger.error(f"PDF generation failed: {e}")
#         raise  # Re-raise to handle upstream

#     return pdf_path


import os
from datetime import datetime
from django.conf import settings
from django.template.loader import render_to_string
from weasyprint import HTML, CSS
import logging

logger = logging.getLogger(__name__)


def generate_pdf_report(booking, booking_type):
    """
    booking_type = 'onsite' | 'offsite'
    """

    if booking_type not in ['onsite', 'offsite']:
        raise ValueError("Invalid booking_type")

    pdf_dir = os.path.join(settings.MEDIA_ROOT, 'pdf_reports')
    os.makedirs(pdf_dir, exist_ok=True)

    safe_name = booking.customer_name.replace(' ', '_')
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    pdf_filename = f"{booking_type}_visit_{safe_name}_{timestamp}.pdf"
    pdf_path = os.path.join(pdf_dir, pdf_filename)

    # TEMPLATE SELECTION
    template_name = (
        'pdf/offsite_confirmation.html'
        if booking_type == 'offsite'
        else 'pdf/onsite_confirmation.html'
    )

    context = {
        'booking': booking,
        'booking_type': booking_type,
        'logo_url': 'static/images/klickit-logo.webp',
        'side_image_url': 'static/images/v1.png',
    }

    html_string = render_to_string(template_name, context)

    # 🔥 DYNAMIC PAGE ORIENTATION
    page_orientation = 'landscape' if booking_type == 'offsite' else 'portrait'

    pdf_css = CSS(string=f"""
        @page {{
            size: A4 {page_orientation};
            margin: 10px;
        }}

        html, body {{
            margin: 0;
            padding: 10px;
            width: 100%;
            height: 100%;
        }}
    """)

    try:
        HTML(
            string=html_string,
            base_url=str(settings.BASE_DIR)
        ).write_pdf(
            pdf_path,
            stylesheets=[pdf_css]
        )

        logger.info(f"PDF generated successfully: {pdf_path}")

    except Exception as e:
        logger.error(f"PDF generation failed: {e}")
        raise

    return pdf_path



def send_booking_email(booking, pdf_path=None, booking_type='onsite'):
    """Send booking confirmation email"""
    
    subject = f"{'Pickup & Delivery' if booking_type == 'onsite' else 'Offsite'} Service Confirmation"
    
    # Get brand-specific logo and link
    brand_logo_url = get_brand_logo_url(booking.brand_name)
    brand_link = get_brand_link(booking.brand_name)
    
    # Prepare context for email template
    payment_method_display = format_payment_method(getattr(booking, 'payment_method', None))
    context = {
        'booking': booking,
        'brand_logo_url': brand_logo_url,
        'brand_link': brand_link,
        'booking_type': booking_type,
        'payment_method_display': payment_method_display,
    }
    
    # Render HTML email
    html_message = render_to_string('bookings/email_template.html', context)
    
    # Choose SMTP credentials and from-email based on booking type
    if booking_type == 'offsite':
        email_user = getattr(settings, 'OFFSITE_EMAIL_USER', settings.EMAIL_HOST_USER)
        email_password = getattr(settings, 'OFFSITE_EMAIL_PASSWORD', settings.EMAIL_HOST_PASSWORD)
        from_email = email_user
    else:
        email_user = getattr(settings, 'ONSITE_EMAIL_USER', settings.EMAIL_HOST_USER)
        email_password = getattr(settings, 'ONSITE_EMAIL_PASSWORD', settings.EMAIL_HOST_PASSWORD)
        from_email = email_user

    # Create an SMTP connection using the selected credentials
    try:
        connection = get_connection(
            host=getattr(settings, 'EMAIL_HOST', None),
            port=getattr(settings, 'EMAIL_PORT', None),
            username=email_user,
            password=email_password,
            use_tls=getattr(settings, 'EMAIL_USE_TLS', False),
            use_ssl=getattr(settings, 'EMAIL_USE_SSL', False),
        )
    except Exception:
        connection = None

    # Set BCC based on booking type
    if booking_type == 'onsite':
        bcc = ['bapu44@gmail.com', 'onsite@klickit.co.in']
    else:
        bcc = ['bapu44@gmail.com', 'cis@klickit.co.in']

    # Create email message with correct from and connection
    email = EmailMessage(
        subject=subject,
        body=html_message,
        from_email=from_email,
        to=[booking.customer_email],
        bcc=bcc,
        connection=connection
    )
    email.content_subtype = 'html'

    # Attach PDF if provided
    if pdf_path and os.path.exists(pdf_path):
        email.attach_file(pdf_path)

    # Send email
    try:
        email.send()
        return True
    except Exception as e:
        # Prefer logging if available; fallback to print for visibility
        try:
            import logging
            logging.getLogger('bookings').exception('Email send failed: %s', e)
        except Exception:
            print(f"Email error: {e}")
        return False


def send_whatsapp_message(phone_number, message, pdf_path=None):
    """
    Send WhatsApp message using Twilio API
    """
    # Twilio credentials (replace with your actual credentials)
    ACCOUNT_SID = ''
    AUTH_TOKEN = ''
    WHATSAPP_FROM = ''
    
    # Format phone number
    if not phone_number.startswith('+'):
        phone_number = '+91' + phone_number
    
    to_number = 'whatsapp:' + phone_number
    
    # Prepare API request
    url = f'https://api.twilio.com/2010-04-01/Accounts/{ACCOUNT_SID}/Messages.json'
    
    data = {
        'To': to_number,
        'From': WHATSAPP_FROM,
        'Body': message,
    }
    
    # Add media URL if PDF provided
    if pdf_path and os.path.exists(pdf_path):
        media_url = f'https://yourdomain.com/{pdf_path}'
        data['MediaUrl'] = media_url
    
    try:
        response = requests.post(
            url,
            data=data,
            auth=(ACCOUNT_SID, AUTH_TOKEN)
        )
        return response.status_code == 201
    except Exception as e:
        print(f"WhatsApp error: {e}")
        return False