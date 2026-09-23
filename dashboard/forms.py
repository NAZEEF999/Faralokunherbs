from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from api.models import SiteSettings, Service, Product, ProductCategory, Promotion, BlogPost
from health.models import AnatomyTopic, HealthCondition, Herb
from .models import StaffAccess

INPUT = 'form-input'


class SiteSettingsForm(forms.ModelForm):
    class Meta:
        model = SiteSettings
        fields = [
            'site_name', 'tagline', 'logo', 'favicon', 'logo_contains_name',
            'primary_color', 'secondary_color', 'accent_color',
            'contact_email', 'contact_phone', 'contact_phone2', 'whatsapp_number', 'whatsapp_greeting',
            'address', 'city', 'country',
            'hero_headline', 'hero_subheadline', 'hero_cta_primary', 'hero_cta_secondary', 'hero_video_url',
            'promo_video_enabled', 'promo_video_title', 'promo_video_description', 'promo_video_url',
            'promo_video_poster', 'promo_video_cta_label', 'promo_video_cta_url',
            'social_facebook', 'social_instagram', 'social_tiktok',
            'footer_description', 'seo_title', 'seo_description', 'seo_keywords',
            'about_title', 'about_description', 'about_mission', 'about_vision', 'registration_no',
            'email_notifications_enabled', 'whatsapp_notifications_enabled',
            'booking_notification_email', 'booking_whatsapp_number',
            'notification_email', 'enquiry_email_notifications_enabled',
            'order_email_notifications_enabled', 'notification_whatsapp_enabled',
            'notification_sound', 'notification_sound_enabled',
        ]
        widgets = {
            'whatsapp_greeting':  forms.Textarea(attrs={'class': INPUT, 'rows': 3}),
            'address':            forms.Textarea(attrs={'class': INPUT, 'rows': 2}),
            'hero_subheadline':   forms.Textarea(attrs={'class': INPUT, 'rows': 3}),
            'promo_video_description': forms.Textarea(attrs={'class': INPUT, 'rows': 3}),
            'footer_description': forms.Textarea(attrs={'class': INPUT, 'rows': 3}),
            'seo_description':    forms.Textarea(attrs={'class': INPUT, 'rows': 2}),
            'seo_keywords':       forms.Textarea(attrs={'class': INPUT, 'rows': 2}),
            'about_description':  forms.Textarea(attrs={'class': INPUT, 'rows': 3}),
            'about_mission':      forms.Textarea(attrs={'class': INPUT, 'rows': 2}),
            'about_vision':       forms.Textarea(attrs={'class': INPUT, 'rows': 2}),
            'primary_color':      forms.TextInput(attrs={'class': INPUT, 'type': 'color'}),
            'secondary_color':    forms.TextInput(attrs={'class': INPUT, 'type': 'color'}),
            'accent_color':       forms.TextInput(attrs={'class': INPUT, 'type': 'color'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name not in self.Meta.widgets:
                field.widget.attrs.setdefault('class', INPUT)

    def clean_contact_phone(self):
        phone = self.cleaned_data.get('contact_phone', '').strip()
        digits = ''.join(c for c in phone if c.isdigit())
        if phone and len(digits) < 8:
            raise forms.ValidationError('Please enter a valid phone number.')
        return phone

    def clean_whatsapp_number(self):
        number = self.cleaned_data.get('whatsapp_number', '').strip()
        digits = ''.join(c for c in number if c.isdigit())
        if number and len(digits) < 8:
            raise forms.ValidationError('Please enter digits only, e.g. 2348012345678.')
        return digits

    def clean_booking_whatsapp_number(self):
        number = self.cleaned_data.get('booking_whatsapp_number', '').strip()
        digits = ''.join(c for c in number if c.isdigit())
        if number and len(digits) < 8:
            raise forms.ValidationError('Please enter digits only, e.g. 2348012345678.')
        return digits

    def clean_notification_sound(self):
        return self.cleaned_data.get('notification_sound') or 'chime'

    def clean_hero_video_url(self):
        url = self.cleaned_data.get('hero_video_url', '').strip()
        return url


class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = ['title', 'short_description', 'description', 'icon_name', 'category',
                  'duration_minutes', 'price', 'image', 'is_featured', 'active', 'sort_order']
        widgets = {
            'short_description': forms.Textarea(attrs={'rows': 2}),
            'description': forms.Textarea(attrs={'rows': 5}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if isinstance(field.widget, (forms.CheckboxInput,)):
                continue
            field.widget.attrs.setdefault('class', INPUT)


class ProductCategoryForm(forms.ModelForm):
    class Meta:
        model = ProductCategory
        fields = ['name', 'description', 'icon_name', 'sort_order', 'is_active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if isinstance(field.widget, (forms.CheckboxInput,)):
                continue
            field.widget.attrs.setdefault('class', INPUT)


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['title', 'short_description', 'description', 'category',
                  'ingredients', 'benefits', 'how_to_use', 'precautions',
                  'price', 'track_stock', 'stock_quantity', 'image', 'local_image',
                  'is_featured', 'active', 'sort_order']
        widgets = {
            'short_description': forms.Textarea(attrs={'rows': 2}),
            'description': forms.Textarea(attrs={'rows': 5}),
            'ingredients': forms.Textarea(attrs={'rows': 4, 'placeholder': 'One ingredient per line'}),
            'benefits': forms.Textarea(attrs={'rows': 4, 'placeholder': 'One benefit per line'}),
            'how_to_use': forms.Textarea(attrs={'rows': 4}),
            'precautions': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if isinstance(field.widget, (forms.CheckboxInput,)):
                continue
            field.widget.attrs.setdefault('class', INPUT)


class PromotionForm(forms.ModelForm):
    class Meta:
        model = Promotion
        fields = ['product', 'discount_type', 'discount_value', 'start_date', 'end_date',
                  'is_active', 'is_featured']
        widgets = {
            'start_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
            'end_date':   forms.DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['start_date'].input_formats = ['%Y-%m-%dT%H:%M']
        self.fields['end_date'].input_formats = ['%Y-%m-%dT%H:%M']
        for name, field in self.fields.items():
            if isinstance(field.widget, (forms.CheckboxInput,)):
                continue
            field.widget.attrs.setdefault('class', INPUT)

    def clean(self):
        cleaned = super().clean()
        start, end = cleaned.get('start_date'), cleaned.get('end_date')
        if start and end and end <= start:
            self.add_error('end_date', 'End date must be after the start date.')
        return cleaned


class BlogPostForm(forms.ModelForm):
    class Meta:
        model = BlogPost
        fields = ['title', 'excerpt', 'content', 'image', 'category', 'author', 'is_published']
        widgets = {
            'excerpt': forms.Textarea(attrs={'rows': 2}),
            'content': forms.Textarea(attrs={'rows': 12}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if isinstance(field.widget, (forms.CheckboxInput,)):
                continue
            field.widget.attrs.setdefault('class', INPUT)


class StaffCreateForm(forms.Form):
    """
    Creates a new dashboard staff account. Deliberately plain forms.Form,
    not a ModelForm on User -- there is no field here that can set
    is_staff/is_superuser, by design (see dashboard.views.staff_add).
    """
    username    = forms.CharField(max_length=150)
    first_name  = forms.CharField(max_length=150, required=False)
    last_name   = forms.CharField(max_length=150, required=False)
    email       = forms.EmailField()
    password1   = forms.CharField(widget=forms.PasswordInput, label='Password')
    password2   = forms.CharField(widget=forms.PasswordInput, label='Confirm Password')
    role        = forms.ChoiceField(choices=StaffAccess.ROLE_CHOICES)
    sections    = forms.MultipleChoiceField(
        choices=StaffAccess.SECTION_CHOICES, required=False,
        widget=forms.CheckboxSelectMultiple,
        help_text='Only used when Role is Custom — other roles get their fixed section set.'
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if isinstance(field.widget, (forms.CheckboxInput, forms.CheckboxSelectMultiple)):
                continue
            field.widget.attrs.setdefault('class', INPUT)

    def clean_username(self):
        username = self.cleaned_data['username'].strip()
        if User.objects.filter(username__iexact=username).exists():
            raise ValidationError('That username is already taken.')
        return username

    def clean_password1(self):
        password = self.cleaned_data['password1']
        validate_password(password)
        return password

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('password1') and cleaned.get('password2') and cleaned['password1'] != cleaned['password2']:
            self.add_error('password2', 'Passwords do not match.')
        return cleaned


class StaffEditForm(forms.ModelForm):
    """
    Edits an existing staff member's role/sections/active status. The
    optional new_password field is a deliberate escape hatch for password
    resets before self-service reset exists — never touches is_staff/
    is_superuser, same as StaffCreateForm.
    """
    sections = forms.MultipleChoiceField(
        choices=StaffAccess.SECTION_CHOICES, required=False,
        widget=forms.CheckboxSelectMultiple,
        help_text='Only used when Role is Custom — other roles get their fixed section set.'
    )
    new_password = forms.CharField(
        widget=forms.PasswordInput, required=False,
        help_text='Leave blank to keep the current password.'
    )

    class Meta:
        model = StaffAccess
        fields = ['role', 'sections', 'is_active']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if isinstance(field.widget, (forms.CheckboxInput, forms.CheckboxSelectMultiple)):
                continue
            field.widget.attrs.setdefault('class', INPUT)

    def clean_new_password(self):
        password = self.cleaned_data.get('new_password', '')
        if password:
            validate_password(password)
        return password

class AnatomyTopicForm(forms.ModelForm):
    class Meta:
        model = AnatomyTopic
        fields = ['name', 'system', 'short_description', 'image', 'function',
                  'common_issues', 'general_info', 'sort_order', 'is_active']
        widgets = {
            'short_description': forms.Textarea(attrs={'rows': 2}),
            'function':          forms.Textarea(attrs={'rows': 3}),
            'common_issues':     forms.Textarea(attrs={'rows': 4, 'placeholder': 'One per line'}),
            'general_info':      forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if isinstance(field.widget, (forms.CheckboxInput,)):
                continue
            field.widget.attrs.setdefault('class', INPUT)


class HealthConditionForm(forms.ModelForm):
    class Meta:
        model = HealthCondition
        fields = ['name', 'image', 'overview', 'causes', 'symptoms', 'prevention',
                  'lifestyle_tips', 'treatment_info', 'seek_care_info', 'related_herbs',
                  'is_featured', 'is_active', 'sort_order']
        widgets = {
            'overview':        forms.Textarea(attrs={'rows': 3}),
            'causes':          forms.Textarea(attrs={'rows': 4, 'placeholder': 'One per line'}),
            'symptoms':        forms.Textarea(attrs={'rows': 4, 'placeholder': 'One per line'}),
            'prevention':      forms.Textarea(attrs={'rows': 4, 'placeholder': 'One per line'}),
            'lifestyle_tips':  forms.Textarea(attrs={'rows': 4, 'placeholder': 'One per line'}),
            'treatment_info':  forms.Textarea(attrs={'rows': 4}),
            'seek_care_info':  forms.Textarea(attrs={'rows': 3}),
            'related_herbs':   forms.CheckboxSelectMultiple,
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if isinstance(field.widget, (forms.CheckboxInput, forms.CheckboxSelectMultiple)):
                continue
            field.widget.attrs.setdefault('class', INPUT)


class HerbForm(forms.ModelForm):
    class Meta:
        model = Herb
        fields = ['common_name', 'scientific_name', 'image', 'description', 'traditional_uses',
                  'compounds_info', 'preparation_info', 'safety_info', 'interactions_info',
                  'precautions', 'related_products', 'is_featured', 'is_active', 'sort_order']
        widgets = {
            'description':       forms.Textarea(attrs={'rows': 3}),
            'traditional_uses':  forms.Textarea(attrs={'rows': 3, 'placeholder': 'One per line'}),
            'compounds_info':    forms.Textarea(attrs={'rows': 3}),
            'preparation_info':  forms.Textarea(attrs={'rows': 3}),
            'safety_info':       forms.Textarea(attrs={'rows': 3}),
            'interactions_info': forms.Textarea(attrs={'rows': 3}),
            'precautions':       forms.Textarea(attrs={'rows': 3}),
            'related_products':  forms.CheckboxSelectMultiple,
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if isinstance(field.widget, (forms.CheckboxInput, forms.CheckboxSelectMultiple)):
                continue
            field.widget.attrs.setdefault('class', INPUT)
