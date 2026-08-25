from django import forms
from .models import Complaint


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
