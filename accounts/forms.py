from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from .models import PatientProfile


class PatientRegisterForm(UserCreationForm):
    first_name = forms.CharField(max_length=50, widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'First name'}))
    last_name  = forms.CharField(max_length=50, widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Last name'}))
    email      = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'your@email.com'}))
    phone      = forms.CharField(max_length=20, required=False, widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': '08012345678 (optional)'}))

    class Meta:
        model  = User
        fields = ['first_name', 'last_name', 'email', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({'class': 'form-input', 'placeholder': 'Create a password'})
        self.fields['password2'].widget.attrs.update({'class': 'form-input', 'placeholder': 'Confirm password'})
        for f in self.fields.values():
            f.help_text = None

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('An account with this email already exists.')
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username   = self.cleaned_data['email']
        user.email      = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name  = self.cleaned_data['last_name']
        if commit:
            user.save()
            PatientProfile.objects.create(
                user=user,
                phone=self.cleaned_data.get('phone', '')
            )
        return user


class PatientLoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class': 'form-input', 'placeholder': 'your@email.com'})
        self.fields['username'].label = 'Email'
        self.fields['password'].widget.attrs.update({'class': 'form-input', 'placeholder': '••••••••'})


class PatientProfileForm(forms.ModelForm):
    first_name = forms.CharField(max_length=50, widget=forms.TextInput(attrs={'class': 'form-input'}))
    last_name  = forms.CharField(max_length=50, widget=forms.TextInput(attrs={'class': 'form-input'}))

    class Meta:
        model  = PatientProfile
        fields = ['phone', 'date_of_birth', 'address']
        widgets = {
            'phone':         forms.TextInput(attrs={'class': 'form-input', 'placeholder': '08012345678'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'address':       forms.Textarea(attrs={'class': 'form-input', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        instance = kwargs.get('instance')
        super().__init__(*args, **kwargs)
        if instance:
            self.fields['first_name'].initial = instance.user.first_name
            self.fields['last_name'].initial  = instance.user.last_name
