from django.contrib import admin
from .models import Complaint


@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display = ('name', 'location', 'detected_area', 'batch_area', 'operation_status', 'fake_risk_score', 'verification_status', 'is_live_photo', 'service_available', 'category', 'ai_waste_type', 'severity', 'ai_confidence', 'status', 'created_at')
    list_filter = ('status', 'operation_status', 'verification_status', 'is_live_photo', 'service_available', 'severity', 'category', 'created_at')
    search_fields = ('name', 'location', 'detected_area', 'batch_area', 'description')
