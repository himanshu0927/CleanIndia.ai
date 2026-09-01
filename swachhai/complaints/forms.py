from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from .models import Complaint, UserProfile


ALLOWED_LOCATION_NAMES = ['gola', 'lakhimpur', 'sitapur', 'lucknow']
MAX_IMAGE_SIZE_MB = 5


class SignupForm(UserCreationForm):
    email = forms.EmailField(
        label='Gmail / Email',
        required=True,
        widget=forms.EmailInput(attrs={'placeholder': 'example@gmail.com'})
    )
    phone_number = forms.CharField(
        label='Phone Number',
        max_length=15,
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Enter phone number'})
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'phone_number', 'password1', 'password2']

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()

        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('This email is already registered.')

        return email

    def clean_phone_number(self):
        phone_number = self.cleaned_data['phone_number'].strip()
        digits_only = phone_number.replace('+', '').replace(' ', '').replace('-', '')

        if not digits_only.isdigit() or len(digits_only) < 10:
            raise forms.ValidationError('Enter a valid phone number.')

        if UserProfile.objects.filter(phone_number=phone_number).exists():
            raise forms.ValidationError('This phone number is already registered.')

        return phone_number

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']

        if commit:
            user.save()
            UserProfile.objects.update_or_create(
                user=user,
                defaults={'phone_number': self.cleaned_data['phone_number']}
            )

        return user


class ComplaintForm(forms.ModelForm):
    class Meta:
        model = Complaint
        fields = ['location', 'latitude', 'longitude', 'category', 'description', 'image']

    def clean_location(self):
        location = self.cleaned_data.get('location', '').strip()

        if len(location) < 3:
            raise ValidationError('Please enter a valid location.')

        location_lower = location.lower()
        if not any(allowed in location_lower for allowed in ALLOWED_LOCATION_NAMES):
            raise ValidationError(
                'Service not available in this area. Available locations: Gola, Lakhimpur, Sitapur, Lucknow.'
            )

        return location

    def clean_latitude(self):
        latitude = self.cleaned_data.get('latitude')

        if latitude is None:
            raise ValidationError('Please select your exact location on the map.')

        if latitude < -90 or latitude > 90:
            raise ValidationError('Invalid GPS latitude.')

        return latitude

    def clean_longitude(self):
        longitude = self.cleaned_data.get('longitude')

        if longitude is None:
            raise ValidationError('Please select your exact location on the map.')

        if longitude < -180 or longitude > 180:
            raise ValidationError('Invalid GPS longitude.')

        return longitude

    def clean_description(self):
        description = self.cleaned_data.get('description', '').strip()

        if len(description) < 10:
            raise ValidationError('Please describe the complaint in at least 10 characters.')

        return description

    def clean_image(self):
        image = self.cleaned_data.get('image')

        if not image:
            raise ValidationError('Please capture and attach a clear garbage/waste photo.')

        if image.size > MAX_IMAGE_SIZE_MB * 1024 * 1024:
            raise ValidationError(f'Image size must be less than {MAX_IMAGE_SIZE_MB} MB.')

        valid_extensions = ['.jpg', '.jpeg', '.png', '.webp']
        name = image.name.lower()

        if not any(name.endswith(extension) for extension in valid_extensions):
            raise ValidationError('Only JPG, PNG, or WEBP images are allowed.')

        return image


class FeedbackForm(forms.ModelForm):
    rating = forms.ChoiceField(choices=[
        (1, '1 - Poor'),
        (2, '2 - Fair'),
        (3, '3 - Good'),
        (4, '4 - Very Good'),
        (5, '5 - Excellent'),
    ])

    class Meta:
        model = Complaint
        fields = ['rating', 'feedback']


class ResolveComplaintForm(forms.ModelForm):
    class Meta:
        model = Complaint
        fields = ['resolved_image']
