from django import forms
from django.core.validators import RegexValidator
from .models import OnsiteVisitService, OffsiteVisitService
import re

class BookingFormBase(forms.Form):
    """Base form for common booking fields"""
    
    # Device Information
    device_name = forms.ChoiceField(
        choices=[
            ('laptop', 'Laptop'),
            ('desktop', 'Desktop'),
            ('allinone', 'All in One'),
            ('ipad', 'iPad'),
        ],
        widget=forms.HiddenInput()
    )
    
    brand_name = forms.ChoiceField(
        choices=[
            ('Acer', 'Acer'),
            ('Apple', 'Apple'),
            ('Asus', 'Asus'),
            ('Dell', 'Dell'),
            ('HP', 'HP'),
            ('Lenovo', 'Lenovo'),
        ]
    )
    
    model_name = forms.CharField(max_length=100)
    
    device_problems = forms.ChoiceField(
        choices=[
            ('Battery Issue', 'Battery Issue'),
            ('Screen Damage', 'Screen Damage'),
            ('Keyboard Malfunction', 'Keyboard Malfunction'),
            ('Overheating', 'Overheating'),
            ('Data Recovery', 'Data Recovery'),
            ('Motherboard Issue', 'Motherboard Issue'),
            ('Booting Problem', 'Booting Problem'),
            ('Hinge Issue', 'Hinge Issue'),
            ('Body Cover Change', 'Body Cover Change'),
            ('Liquid/Water Spill', 'Liquid/Water Spill'),
            ('Touch Pad Issue', 'Touch Pad Issue'),
            ('HDD Issue', 'HDD Issue'),
            ('Operating System Issue', 'Operating System Issue'),
            ('Mic/Speaker Issue', 'Mic/Speaker Issue'),
            ('Charging Problem', 'Charging Problem'),
            ('Display Issue', 'Display Issue'),
            ('Other', 'Other'),
        ]
    )
    
    serial_number = forms.CharField(max_length=100, required=False)
    write_issue = forms.CharField(widget=forms.Textarea, min_length=2)
    
    # Customer Information
    customer_name = forms.CharField(
        max_length=200,
        min_length=2,
        widget=forms.TextInput(attrs={'placeholder': 'Enter your name'})
    )
    
    customer_email = forms.EmailField(
        widget=forms.EmailInput(attrs={'placeholder': 'Enter your email'})
    )
    
    phone_regex = RegexValidator(
        regex=r'^\d{10}$',
        message="Phone number must be 10 digits"
    )
    customer_mobile_number = forms.CharField(
        validators=[phone_regex],
        max_length=10,
        widget=forms.TextInput(attrs={'placeholder': 'Enter your mobile number'})
    )
    
    customer_address_home = forms.CharField(
        widget=forms.Textarea(attrs={'placeholder': 'Enter your address', 'rows': 3})
    )
    
    # Service Details
    selected_slotservice = forms.ChoiceField(
        choices=[
            ('Andheri', 'Andheri'),
            ('Thane', 'Thane'),
            ('Dadar', 'Dadar'),
        ]
    )
    
    booking_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    
    def clean_customer_email(self):
        email = self.cleaned_data.get('customer_email')
        if email and not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email):
            raise forms.ValidationError("Please enter a valid email address")
        return email
    
    def clean_booking_date(self):
        from datetime import date
        booking_date = self.cleaned_data.get('booking_date')
        
        if booking_date:
            # Check if date is not in past
            if booking_date < date.today():
                raise forms.ValidationError("Booking date cannot be in the past")
            
            # Check if Sunday
            if booking_date.weekday() == 6:  # Sunday = 6
                raise forms.ValidationError("Service is not available on Sunday")
            
            # Check if holiday
            from .models import Holiday
            if Holiday.objects.filter(date=booking_date).exists():
                raise forms.ValidationError("Service is not available on this holiday")
        
        return booking_date


class OffsiteBookingForm(BookingFormBase):
    """Form for offsite/walk-in bookings"""
    
    service_types = forms.CharField(
        initial='Visit Service Center',
        widget=forms.HiddenInput()
    )
    
    time_slots = forms.ChoiceField(
        choices=[
            ('10:00 AM - 11:00 AM', '10:00 AM - 11:00 AM'),
            ('11:00 AM - 12:00 PM', '11:00 AM - 12:00 PM'),
            ('12:00 PM - 01:00 PM', '12:00 PM - 01:00 PM'),
            ('01:00 PM - 02:00 PM', '01:00 PM - 02:00 PM'),
            ('02:00 PM - 03:00 PM', '02:00 PM - 03:00 PM'),
            ('03:00 PM - 04:00 PM', '03:00 PM - 04:00 PM'),
            ('04:00 PM - 05:00 PM', '04:00 PM - 05:00 PM'),
            ('05:00 PM - 06:00 PM', '05:00 PM - 06:00 PM'),
            ('06:00 PM - 07:00 PM', '06:00 PM - 07:00 PM'),
        ]
    )
    
    website_url = forms.URLField(
        initial='https://klickit.co.in',
        widget=forms.HiddenInput()
    )
    
    def clean(self):
        cleaned_data = super().clean()
        booking_date = cleaned_data.get('booking_date')
        time_slots = cleaned_data.get('time_slots')
        selected_slotservice = cleaned_data.get('selected_slotservice')
        
        if booking_date and time_slots and selected_slotservice:
            # Check if slot already has 2 bookings (max for offsite)
            existing_bookings = OffsiteVisitService.objects.filter(
                booking_date=booking_date,
                select_time_slot=time_slots,
                service_center_name=selected_slotservice
            ).count()
            
            if existing_bookings >= 2:
                raise forms.ValidationError("This time slot is fully booked. Please select another slot.")
        
        return cleaned_data


class OnsiteBookingForm(BookingFormBase):
    """Form for onsite bookings with payment"""
    
    service_types = forms.CharField(
        initial='Pickup & Drop - Service Charges',
        widget=forms.HiddenInput()
    )
    
    time_slots = forms.ChoiceField(
        choices=[
            ('10:00 AM - 12:00 PM', '10:00 AM - 12:00 PM'),
            ('12:00 PM - 02:00 PM', '12:00 PM - 02:00 PM'),
            ('02:00 PM - 04:00 PM', '02:00 PM - 04:00 PM'),
            ('04:00 PM - 06:00 PM', '04:00 PM - 06:00 PM'),
        ]
    )
    
    # Pricing fields (hidden, calculated on frontend)
    pick_up_drop_charge = forms.DecimalField(widget=forms.HiddenInput())
    diagnostic_charges = forms.DecimalField(widget=forms.HiddenInput())
    total_charges = forms.DecimalField(widget=forms.HiddenInput())
    
    website_url = forms.URLField(
        initial='https://klickit.co.in',
        widget=forms.HiddenInput()
    )
    
    def clean(self):
        cleaned_data = super().clean()
        booking_date = cleaned_data.get('booking_date')
        time_slots = cleaned_data.get('time_slots')
        selected_slotservice = cleaned_data.get('selected_slotservice')
        
        if booking_date and time_slots and selected_slotservice:
            # Check if slot already has 1 booking (max for onsite)
            existing_bookings = OnsiteVisitService.objects.filter(
                booking_date=booking_date,
                select_time_slot=time_slots,
                service_center_name=selected_slotservice,
                payment_status__in=['PENDING', 'SUCCESS']
            ).count()
            
            if existing_bookings >= 1:
                raise forms.ValidationError("This time slot is fully booked. Please select another slot.")
        
        return cleaned_data
    
    def clean_total_charges(self):
        total = self.cleaned_data.get('total_charges')
        if total and total <= 0:
            raise forms.ValidationError("Invalid total amount")
        return total