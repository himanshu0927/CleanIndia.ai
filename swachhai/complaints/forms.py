from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Complaint
from .models import UserProfile


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
            UserProfile.objects.create(
                user=user,
                phone_number=self.cleaned_data['phone_number']
            )

        return user


class ComplaintForm(forms.ModelForm):
    class Meta:
        model = Complaint
        fields = ['location', 'latitude', 'longitude', 'category', 'description', 'image']


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
