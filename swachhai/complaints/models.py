from django.contrib.auth.models import User
from django.db import models


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone_number = models.CharField(max_length=15)

    def __str__(self):
        return f'{self.user.username} profile'


class Complaint(models.Model):
    CATEGORY_CHOICES = [
        ('garbage', 'Garbage'),
        ('overflowing_bin', 'Overflowing Bin'),
        ('illegal_dumping', 'Illegal Dumping'),
        ('drainage', 'Drainage Issue'),
        ('other', 'Other'),
    ]
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('In Progress', 'In Progress'),
        ('Resolved', 'Resolved'),
    ]
    OPERATION_STATUS_CHOICES = [
        ('Waiting for Batch', 'Waiting for Batch'),
        ('Ready for Pickup', 'Ready for Pickup'),
        ('Vehicle Assigned', 'Vehicle Assigned'),
        ('Cleanup Done', 'Cleanup Done'),
    ]
    WASTE_TYPE_CHOICES = [
        ('Plastic', 'Plastic'),
        ('Wet Waste', 'Wet Waste'),
        ('Dry Waste', 'Dry Waste'),
        ('E-Waste', 'E-Waste'),
        ('Glass', 'Glass'),
        ('Metal', 'Metal'),
        ('Construction Waste', 'Construction Waste'),
        ('Other', 'Other'),
    ]
    SEVERITY_CHOICES = [
        ('Low', 'Low'),
        ('Medium', 'Medium'),
        ('High', 'High'),
        ('Critical', 'Critical'),
    ]

    name = models.CharField(max_length=100)
    location = models.CharField(max_length=200)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    detected_area = models.CharField(max_length=255, default='Unknown')
    service_available = models.BooleanField(default=False)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    description = models.TextField()
    image = models.ImageField(upload_to='garbage_images/')
    resolved_image = models.ImageField(upload_to='resolved_images/', null=True, blank=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Pending')
    operation_status = models.CharField(max_length=50, choices=OPERATION_STATUS_CHOICES, default='Waiting for Batch')
    batch_area = models.CharField(max_length=150, default='Unassigned')
    fake_risk_score = models.IntegerField(default=0)
    verification_status = models.CharField(max_length=50, default='Pending Verification')
    is_live_photo = models.BooleanField(default=False)
    ai_result = models.CharField(max_length=100, default='Not analyzed')
    ai_confidence = models.IntegerField(default=85)
    ai_waste_type = models.CharField(max_length=50, choices=WASTE_TYPE_CHOICES, default='Other')
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='Medium')
    created_at = models.DateTimeField(auto_now_add=True)
    in_progress_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    rating = models.IntegerField(null=True, blank=True)
    feedback = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.location
