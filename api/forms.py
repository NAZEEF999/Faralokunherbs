from django import forms
from .models import Appointment, Inquiry, Order, Subscriber, Testimonial


class AppointmentForm(forms.ModelForm):
    appointment_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-input'
        }),
        required=False,
        error_messages={'invalid': 'Please enter a valid date.'}
    )

    class Meta:
        model = Appointment
        fields = ['service', 'appointment_date', 'preferred_time',
                  'contact_name', 'contact_email', 'contact_phone', 'notes']
        widgets = {
            'service':        forms.Select(attrs={'class': 'form-input'}),
            'preferred_time': forms.Select(attrs={'class': 'form-input'}),
            'contact_name':   forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Your full name'
            }),
            'contact_email':  forms.EmailInput(attrs={
                'class': 'form-input',
                'placeholder': 'your@email.com'
            }),
            'contact_phone':  forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': '08012345678'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-input',
                'rows': 4,
                'placeholder': 'Describe your condition briefly...'
            }),
        }
        error_messages = {
            'contact_name': {
                'required': 'Please enter your full name.',
                'max_length': 'Name is too long.',
            },
            'contact_phone': {
                'required': 'Please enter your phone number so we can contact you.',
            },
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from .models import Service
        self.fields['service'].queryset    = Service.objects.filter(active=True)
        self.fields['service'].empty_label = '— Select a Service —'
        self.fields['service'].required    = False
        self.fields['contact_name'].label  = 'Full Name'
        self.fields['contact_phone'].label = 'Phone Number'
        self.fields['contact_email'].label = 'Email (optional)'
        self.fields['contact_email'].required = False
        self.fields['notes'].required         = False
        self.fields['preferred_time'].required = False
        self.fields['appointment_date'].required = False

    def clean_contact_name(self):
        name = self.cleaned_data.get('contact_name', '').strip()
        if not name:
            raise forms.ValidationError('Please enter your full name.')
        if len(name) < 2:
            raise forms.ValidationError('Please enter your full name, not just an initial.')
        return name

    def clean_contact_phone(self):
        phone = self.cleaned_data.get('contact_phone', '').strip()
        if not phone:
            raise forms.ValidationError('Please enter your phone number.')
        digits = ''.join(c for c in phone if c.isdigit())
        if len(digits) < 8:
            raise forms.ValidationError('Please enter a valid phone number.')
        return phone

    def clean_contact_email(self):
        email = self.cleaned_data.get('contact_email', '').strip()
        if email and '@' not in email:
            raise forms.ValidationError('Please enter a valid email address.')
        return email

    def clean_appointment_date(self):
        from django.utils import timezone
        date = self.cleaned_data.get('appointment_date')
        if date and date < timezone.localdate():
            raise forms.ValidationError('Appointment date cannot be in the past.')
        return date

    def clean(self):
        cleaned = super().clean()
        # No practitioner roster anymore -- the business handles one
        # confirmed consultation per date+time slot. This just checks that
        # slot isn't already CONFIRMED for someone else; two PENDING
        # requests for the same slot are fine (staff resolves it).
        appt_date = cleaned.get('appointment_date')
        appt_time = cleaned.get('preferred_time')
        if appt_date and appt_time:
            if not Appointment.slot_is_available(appt_date, appt_time):
                raise forms.ValidationError(
                    'That appointment time is already booked. Please select another available time.'
                )
        return cleaned


class InquiryForm(forms.ModelForm):
    class Meta:
        model = Inquiry
        fields = ['name', 'email', 'phone', 'message']
        widgets = {
            'name':    forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Your full name'
            }),
            'email':   forms.EmailInput(attrs={
                'class': 'form-input',
                'placeholder': 'your@email.com (optional)'
            }),
            'phone':   forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': '08012345678 (optional)'
            }),
            'message': forms.Textarea(attrs={
                'class': 'form-input',
                'rows': 5,
                'placeholder': 'Type your message here...'
            }),
        }
        error_messages = {
            'name':    {'required': 'Please enter your name.'},
            'message': {'required': 'Please enter your message.'},
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].required = False
        self.fields['phone'].required = False

    def clean_name(self):
        name = self.cleaned_data.get('name', '').strip()
        if not name:
            raise forms.ValidationError('Please enter your name.')
        if len(name) < 2:
            raise forms.ValidationError('Please enter your full name.')
        return name

    def clean_message(self):
        message = self.cleaned_data.get('message', '').strip()
        if not message:
            raise forms.ValidationError('Please enter your message.')
        if len(message) < 10:
            raise forms.ValidationError('Please write a bit more detail in your message.')
        return message


class AddToCartForm(forms.Form):
    quantity = forms.IntegerField(
        min_value=1,
        initial=1,
        widget=forms.NumberInput(attrs={
            'class': 'form-input',
            'min': '1'
        }),
        error_messages={
            'required': 'Please enter a quantity.',
            'min_value': 'Quantity must be at least 1.',
        }
    )


class ProductEnquiryForm(forms.ModelForm):
    """'Contact for Enquiry' form that replaces the Add-to-Cart / Buy path
    for the public shop. The customer names the product, the quantity they
    want, how to reach them and their question -- the business replies with
    the price and next steps. No price data ever reaches this form."""
    product_id = forms.IntegerField(widget=forms.HiddenInput(), required=True)
    product_name = forms.CharField(widget=forms.HiddenInput(), required=False)
    quantity = forms.IntegerField(
        min_value=1,
        initial=1,
        widget=forms.NumberInput(attrs={
            'class': 'form-input',
            'min': '1',
            'placeholder': 'Quantity'
        }),
        error_messages={
            'required': 'Please enter a quantity.',
            'min_value': 'Quantity must be at least 1.',
        }
    )

    class Meta:
        model = Inquiry
        fields = ['name', 'phone', 'message']
        widgets = {
            'name':    forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Your full name'
            }),
            'phone':   forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Your phone number'
            }),
            'message': forms.Textarea(attrs={
                'class': 'form-input',
                'rows': 4,
                'placeholder': 'Questions for us? e.g. availability, sizing, delivery…'
            }),
        }
        error_messages = {
            'name':    {'required': 'Please enter your name.'},
            'phone':   {'required': 'Please enter your phone number so we can reply.'},
            'message': {'required': 'Please tell us a little about what you need.'},
        }

    def __init__(self, *args, **kwargs):
        if kwargs.get('instance') is None:
            kwargs['instance'] = Inquiry()
        super().__init__(*args, **kwargs)
        # Inquiry.phone is blank=True at the model level (the generic contact
        # form allows it), but the enquiry path needs a number to reply on.
        self.fields['phone'].required = True
        self.fields['email'] = forms.EmailField(
            required=False,
            widget=forms.EmailInput(attrs={
                'class': 'form-input',
                'placeholder': 'your@email.com (optional)'
            }),
        )

    def clean_quantity(self):
        try:
            qty = int(self.cleaned_data.get('quantity'))
        except (TypeError, ValueError):
            raise forms.ValidationError('Please enter a valid quantity.')
        if qty < 1:
            raise forms.ValidationError('Quantity must be at least 1.')
        return qty

    def clean_product_id(self):
        from .models import Product
        pid = self.cleaned_data.get('product_id')
        if not pid or not Product.objects.filter(id=pid, active=True).exists():
            raise forms.ValidationError('Please enquire from the product page.')
        return pid


class CheckoutForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['customer_name', 'customer_phone', 'customer_email', 'delivery_address', 'notes']
        widgets = {
            'customer_name': forms.TextInput(attrs={
                'class': 'form-input', 'placeholder': 'Your full name'
            }),
            'customer_phone': forms.TextInput(attrs={
                'class': 'form-input', 'placeholder': '08012345678'
            }),
            'customer_email': forms.EmailInput(attrs={
                'class': 'form-input', 'placeholder': 'your@email.com (optional)'
            }),
            'delivery_address': forms.Textarea(attrs={
                'class': 'form-input', 'rows': 3, 'placeholder': 'Delivery address (optional)'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-input', 'rows': 2, 'placeholder': 'Anything else we should know? (optional)'
            }),
        }
        error_messages = {
            'customer_name':  {'required': 'Please enter your full name.'},
            'customer_phone': {'required': 'Please enter your phone number.'},
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['customer_email'].required = False
        self.fields['delivery_address'].required = False
        self.fields['notes'].required = False

    def clean_customer_name(self):
        name = self.cleaned_data.get('customer_name', '').strip()
        if not name:
            raise forms.ValidationError('Please enter your full name.')
        if len(name) < 2:
            raise forms.ValidationError('Please enter your full name.')
        return name

    def clean_customer_phone(self):
        phone = self.cleaned_data.get('customer_phone', '').strip()
        if not phone:
            raise forms.ValidationError('Please enter your phone number.')
        digits = ''.join(c for c in phone if c.isdigit())
        if len(digits) < 8:
            raise forms.ValidationError('Please enter a valid phone number.')
        return phone


class SubscriberForm(forms.ModelForm):
    class Meta:
        model = Subscriber
        fields = ['email']
        widgets = {
            'email': forms.EmailInput(attrs={
                'class': 'bg-forest-mid/60 border border-healing/20 rounded-lg px-4 py-2.5 text-leaf text-sm placeholder-sage/50 focus:outline-none focus:border-healing/50 transition-all flex-1',
                'placeholder': 'Your email address'
            })
        }
        error_messages = {
            'email': {'required': 'Please enter your email address.'}
        }


class TestimonialForm(forms.ModelForm):
    class Meta:
        model = Testimonial
        fields = ['name', 'location', 'content', 'condition', 'rating']
        widgets = {
            'name':      forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Your name'
            }),
            'location':  forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Lagos, Nigeria'
            }),
            'content':   forms.Textarea(attrs={
                'class': 'form-input',
                'rows': 4,
                'placeholder': 'Share your healing experience...'
            }),
            'condition': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'e.g. Fibroid Treatment'
            }),
            'rating':    forms.Select(
                attrs={'class': 'form-input'},
                choices=[(i, f'{i} Star{"s" if i > 1 else ""}') for i in range(1, 6)]
            ),
        }
        error_messages = {
            'name':    {'required': 'Please enter your name.'},
            'content': {'required': 'Please share your experience.'},
        }