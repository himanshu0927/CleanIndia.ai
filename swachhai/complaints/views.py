import csv
import math
from collections import defaultdict
from datetime import timedelta

from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.db import DatabaseError
from django.db.models import Avg
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.utils import timezone
from .ai_detector import AIDetectorSetupError, detect_garbage_image, validate_actual_image_content
from .forms import ComplaintForm, FeedbackForm, ResolveComplaintForm, SignupForm
from .models import Complaint


def detect_waste_type(category):
    if category == 'garbage':
        return 'Dry Waste', 88
    elif category == 'overflowing_bin':
        return 'Wet Waste', 84
    elif category == 'illegal_dumping':
        return 'Construction Waste', 90
    elif category == 'drainage':
        return 'Wet Waste', 82
    else:
        return 'Other', 75


def calculate_severity(waste_type, category):
    if waste_type == 'Construction Waste':
        return 'High'
    elif waste_type == 'E-Waste':
        return 'High'
    elif category == 'overflowing_bin':
        return 'High'
    elif category == 'illegal_dumping':
        return 'Critical'
    elif category == 'drainage':
        return 'High'
    elif waste_type in ['Plastic', 'Wet Waste']:
        return 'Medium'
    else:
        return 'Low'


def calculate_distance_km(lat1, lon1, lat2, lon2):
    earth_radius = 6371

    lat1 = math.radians(float(lat1))
    lon1 = math.radians(float(lon1))
    lat2 = math.radians(float(lat2))
    lon2 = math.radians(float(lon2))

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    )

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return earth_radius * c


def get_available_service_city(latitude, longitude):
    for city in settings.SERVICE_CITIES:
        distance = calculate_distance_km(
            latitude,
            longitude,
            city['latitude'],
            city['longitude']
        )

        if distance <= city['radius_km']:
            return city

    return None


def is_service_open_now():
    current_time = timezone.localtime().time()
    return settings.SERVICE_OPEN_HOUR <= current_time.hour < settings.SERVICE_CLOSE_HOUR


def update_batch_status(new_complaint):
    nearby_complaints = []
    active_complaints = Complaint.objects.exclude(status='Resolved')

    for complaint in active_complaints:
        if complaint.latitude is not None and complaint.longitude is not None:
            distance = calculate_distance_km(
                new_complaint.latitude,
                new_complaint.longitude,
                complaint.latitude,
                complaint.longitude
            )

            if distance <= settings.BATCH_RADIUS_KM:
                nearby_complaints.append(complaint)

    batch_area = new_complaint.location

    if len(nearby_complaints) >= settings.MIN_COMPLAINTS_FOR_PICKUP:
        for complaint in nearby_complaints:
            complaint.operation_status = 'Ready for Pickup'
            complaint.batch_area = batch_area
            complaint.save()
    else:
        new_complaint.operation_status = 'Waiting for Batch'
        new_complaint.batch_area = batch_area
        new_complaint.save()


def calculate_fake_risk_score(complaint, request):
    score = 0

    if complaint.latitude is None or complaint.longitude is None:
        score += 40

    if not complaint.service_available:
        score += 50

    if not complaint.image:
        score += 30

    is_live_photo = request.POST.get('is_live_photo') == 'true'
    complaint.is_live_photo = is_live_photo

    if not is_live_photo:
        score += 15

    recent_time = timezone.now() - timedelta(minutes=10)

    recent_user_complaints = Complaint.objects.filter(
        name=request.user.username,
        created_at__gte=recent_time
    ).count()

    if recent_user_complaints >= 3:
        score += 25

    nearby_active_complaints = 0

    for existing in Complaint.objects.exclude(status='Resolved'):
        if (
            existing.latitude is not None
            and existing.longitude is not None
            and complaint.latitude is not None
            and complaint.longitude is not None
        ):
            distance = calculate_distance_km(
                complaint.latitude,
                complaint.longitude,
                existing.latitude,
                existing.longitude
            )

            if distance <= 0.2:
                nearby_active_complaints += 1

    if nearby_active_complaints > 0:
        score += 20

    if score > 100:
        score = 100

    return score


def home(request):
    total = Complaint.objects.count()
    pending = Complaint.objects.filter(status='Pending').count()
    in_progress = Complaint.objects.filter(status='In Progress').count()
    resolved = Complaint.objects.filter(status='Resolved').count()

    return render(request, 'home.html', {
        'total': total,
        'pending': pending,
        'in_progress': in_progress,
        'resolved': resolved,
    })


def user_signup_view(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                user.is_staff = False
                user.save()
                login(request, user)
                messages.success(request, 'Signup complete. Welcome to CleanIndia.ai!')
                return redirect('home')
            except DatabaseError:
                form.add_error(None, 'Signup could not be completed right now. Please try again.')
    else:
        form = SignupForm()

    return render(request, 'user_signup.html', {'form': form})


def authority_signup_view(request):
    authority_code_error = None

    if request.method == 'POST':
        form = SignupForm(request.POST)
        authority_code = request.POST.get('authority_code', '').strip()

        if authority_code != settings.AUTHORITY_SIGNUP_CODE:
            authority_code_error = 'Invalid authority code.'
        elif form.is_valid():
            try:
                user = form.save()
                user.is_staff = True
                user.save()
                login(request, user)
                messages.success(request, 'Authority signup complete. Welcome to the municipal dashboard!')
                return redirect('dashboard')
            except DatabaseError:
                form.add_error(None, 'Authority signup could not be completed right now. Please try again.')
    else:
        form = SignupForm()

    return render(request, 'authority_signup.html', {
        'form': form,
        'authority_code_error': authority_code_error,
    })


def user_login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            try:
                user = form.get_user()

                if user.is_staff:
                    form.add_error(None, 'Authority account detected. Please use Authority Login.')
                else:
                    login(request, user)
                    return redirect('home')
            except DatabaseError:
                form.add_error(None, 'Login failed. Please try again.')
    else:
        form = AuthenticationForm()

    return render(request, 'user_login.html', {'form': form})


def authority_login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            try:
                user = form.get_user()

                if not user.is_staff:
                    form.add_error(None, 'Only authority/staff accounts can login here.')
                else:
                    login(request, user)
                    return redirect('dashboard')
            except DatabaseError:
                form.add_error(None, 'Authority login failed. Please try again.')
    else:
        form = AuthenticationForm()

    return render(request, 'authority_login.html', {'form': form})


signup_view = user_signup_view


def logout_view(request):
    logout(request)
    return redirect('home')


@login_required
def report_complaint(request):
    report_context = {
        'service_cities': settings.SERVICE_CITIES,
        'service_open_hour': settings.SERVICE_OPEN_HOUR,
        'service_close_hour': settings.SERVICE_CLOSE_HOUR,
    }

    if request.method == 'POST':
        form = ComplaintForm(request.POST, request.FILES)
        if form.is_valid():
            if not is_service_open_now():
                form.add_error(
                    None,
                    'Service is available only between 8 AM and 5 PM. Please submit your complaint during service hours.'
                )
                return render(request, 'report.html', {**report_context, 'form': form})

            allowed_locations = ['gola', 'lakhimpur', 'sitapur', 'lucknow']
            location = (form.cleaned_data.get('location') or '').lower().strip()
            is_allowed = False

            for allowed_location in allowed_locations:
                if allowed_location in location:
                    is_allowed = True
                    break

            if not is_allowed:
                form.add_error(
                    'location',
                    'Service not available in this area. Available locations: Gola, Lakhimpur, Sitapur, Lucknow.'
                )
                return render(request, 'report.html', {**report_context, 'form': form})

            latitude = form.cleaned_data.get('latitude')
            longitude = form.cleaned_data.get('longitude')

            if latitude is None or longitude is None:
                form.add_error(None, 'Please capture your GPS location before submitting complaint.')
                return render(request, 'report.html', {**report_context, 'form': form})

            service_city = get_available_service_city(latitude, longitude)

            if not service_city:
                form.add_error(None, 'Service not available in this area.')
                return render(request, 'report.html', {**report_context, 'form': form})

            is_live_photo = request.POST.get('is_live_photo') == 'true'

            if not is_live_photo:
                form.add_error(None, 'Please capture a live garbage photo using the camera.')
                return render(request, 'report.html', {**report_context, 'form': form})

            uploaded_image = request.FILES.get('image')

            if not uploaded_image:
                form.add_error(None, 'Please capture a live garbage photo.')
                return render(request, 'report.html', {**report_context, 'form': form})

            image_is_valid, image_error = validate_actual_image_content(uploaded_image)

            if not image_is_valid:
                form.add_error(None, image_error)
                return render(request, 'report.html', {**report_context, 'form': form})

            try:
                ai_waste_type, ai_confidence = detect_garbage_image(uploaded_image)
            except AIDetectorSetupError as error:
                ai_waste_type, ai_confidence = detect_waste_type(form.cleaned_data.get('category'))

            if ai_waste_type == 'Not Garbage' or ai_confidence < 70:
                form.add_error(
                    None,
                    'Invalid complaint photo. Please capture a clear garbage or waste image.'
                )
                return render(request, 'report.html', {**report_context, 'form': form})

            complaint = form.save(commit=False)
            complaint.name = request.user.username
            complaint.detected_area = service_city['name']
            complaint.service_available = True
            complaint.is_live_photo = is_live_photo
            complaint.ai_waste_type = ai_waste_type
            complaint.ai_confidence = ai_confidence
            complaint.ai_result = f'AI detected: {ai_waste_type}'
            complaint.severity = calculate_severity(ai_waste_type, complaint.category)
            complaint.fake_risk_score = calculate_fake_risk_score(complaint, request)

            if complaint.fake_risk_score >= 61:
                complaint.verification_status = 'High Risk - Needs Review'
            elif complaint.fake_risk_score >= 31:
                complaint.verification_status = 'Medium Risk'
            else:
                complaint.verification_status = 'Verified'

            complaint.save()
            update_batch_status(complaint)
            return redirect('my_complaints')
    else:
        form = ComplaintForm()

    return render(request, 'report.html', {**report_context, 'form': form})


@staff_member_required
def dashboard(request):
    complaints = Complaint.objects.all()

    status_filter = request.GET.get('status')
    operation_status_filter = request.GET.get('operation_status')
    category_filter = request.GET.get('category')
    search_query = request.GET.get('q')

    if status_filter:
        complaints = complaints.filter(status=status_filter)

    if operation_status_filter:
        complaints = complaints.filter(operation_status=operation_status_filter)

    if category_filter:
        complaints = complaints.filter(category=category_filter)

    if search_query:
        complaints = complaints.filter(location__icontains=search_query)

    severity_order = {
        'Critical': 1,
        'High': 2,
        'Medium': 3,
        'Low': 4,
    }

    complaints = sorted(
        complaints,
        key=lambda complaint: (
            severity_order.get(complaint.severity, 5),
            -complaint.created_at.timestamp()
        )
    )

    total = Complaint.objects.count()
    pending = Complaint.objects.filter(status='Pending').count()
    waiting_for_batch = Complaint.objects.filter(operation_status='Waiting for Batch').count()
    ready_for_pickup = Complaint.objects.filter(operation_status='Ready for Pickup').count()
    in_progress = Complaint.objects.filter(status='In Progress').count()
    resolved = Complaint.objects.filter(status='Resolved').count()
    feedback_count = Complaint.objects.filter(rating__isnull=False).count()
    average_rating = Complaint.objects.filter(rating__isnull=False).aggregate(Avg('rating'))['rating__avg']

    if average_rating:
        average_rating = round(average_rating, 1)
    else:
        average_rating = 0

    area_groups = defaultdict(list)

    for complaint in Complaint.objects.exclude(status='Resolved'):
        area_groups[complaint.batch_area].append(complaint)

    return render(request, 'dashboard.html', {
        'complaints': complaints,
        'total': total,
        'pending': pending,
        'waiting_for_batch': waiting_for_batch,
        'ready_for_pickup': ready_for_pickup,
        'in_progress': in_progress,
        'resolved': resolved,
        'feedback_count': feedback_count,
        'average_rating': average_rating,
        'area_groups': dict(area_groups),
        'status_filter': status_filter,
        'operation_status_filter': operation_status_filter,
        'category_filter': category_filter,
        'search_query': search_query,
    })


@staff_member_required
def export_complaints_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="cleanindia_complaints.csv"'

    writer = csv.writer(response)

    writer.writerow([
        'ID',
        'Name',
        'Location',
        'Detected Area',
        'Service Available',
        'Category',
        'Description',
        'Status',
        'Operation Status',
        'Batch Area',
        'Fake Risk Score',
        'Verification Status',
        'Live Photo',
        'Severity',
        'AI Result',
        'AI Waste Type',
        'AI Confidence',
        'Rating',
        'Feedback',
        'Created At',
        'In Progress At',
        'Resolved At'
    ])

    complaints = Complaint.objects.all().order_by('-created_at')

    for complaint in complaints:
        writer.writerow([
            complaint.id,
            complaint.name,
            complaint.location,
            complaint.detected_area,
            complaint.service_available,
            complaint.category,
            complaint.description,
            complaint.status,
            complaint.operation_status,
            complaint.batch_area,
            complaint.fake_risk_score,
            complaint.verification_status,
            complaint.is_live_photo,
            complaint.severity,
            complaint.ai_result,
            complaint.ai_waste_type,
            complaint.ai_confidence,
            complaint.rating,
            complaint.feedback,
            complaint.created_at,
            complaint.in_progress_at,
            complaint.resolved_at
        ])

    return response


@login_required
def my_complaints(request):
    complaints = Complaint.objects.filter(name=request.user.username).order_by('-created_at')

    return render(request, 'my_complaints.html', {
        'complaints': complaints
    })


@login_required
def complaint_detail(request, complaint_id):
    complaint = Complaint.objects.get(id=complaint_id)

    if not request.user.is_staff and complaint.name != request.user.username:
        return redirect('my_complaints')

    return render(request, 'complaint_detail.html', {
        'complaint': complaint
    })


@login_required
def submit_feedback(request, complaint_id):
    complaint = Complaint.objects.get(id=complaint_id)

    if complaint.name != request.user.username:
        return redirect('my_complaints')

    if complaint.status != 'Resolved':
        return redirect('complaint_detail', complaint_id=complaint.id)

    if request.method == 'POST':
        form = FeedbackForm(request.POST, instance=complaint)
        if form.is_valid():
            form.save()
            return redirect('complaint_detail', complaint_id=complaint.id)
    else:
        form = FeedbackForm(instance=complaint)

    return render(request, 'feedback.html', {
        'form': form,
        'complaint': complaint
    })


@staff_member_required
def resolve_with_proof(request, complaint_id):
    complaint = Complaint.objects.get(id=complaint_id)

    if request.method == 'POST':
        form = ResolveComplaintForm(request.POST, request.FILES, instance=complaint)
        if form.is_valid():
            complaint = form.save(commit=False)
            complaint.status = 'Resolved'
            complaint.operation_status = 'Cleanup Done'

            if not complaint.resolved_at:
                complaint.resolved_at = timezone.now()

            complaint.save()
            return redirect('complaint_detail', complaint_id=complaint.id)
    else:
        form = ResolveComplaintForm(instance=complaint)

    return render(request, 'resolve_with_proof.html', {
        'form': form,
        'complaint': complaint
    })


@staff_member_required
def resolve_complaint(request, complaint_id):
    complaint = Complaint.objects.get(id=complaint_id)
    complaint.status = 'Resolved'
    complaint.operation_status = 'Cleanup Done'

    if not complaint.resolved_at:
        complaint.resolved_at = timezone.now()

    complaint.save()
    return redirect('dashboard')


@staff_member_required
def delete_complaint(request, complaint_id):
    complaint = Complaint.objects.get(id=complaint_id)

    if request.method == 'POST':
        complaint.delete()
        return redirect('dashboard')

    return redirect('complaint_detail', complaint_id=complaint.id)


@staff_member_required
def update_status(request, complaint_id, status):
    complaint = Complaint.objects.get(id=complaint_id)

    if status in ['Pending', 'In Progress', 'Resolved']:
        complaint.status = status

        if status == 'In Progress' and not complaint.in_progress_at:
            complaint.in_progress_at = timezone.now()

        if status == 'Resolved' and not complaint.resolved_at:
            complaint.resolved_at = timezone.now()
            complaint.operation_status = 'Cleanup Done'

        complaint.save()

    return redirect('dashboard')


@staff_member_required
def update_operation_status(request, complaint_id, operation_status):
    complaint = Complaint.objects.get(id=complaint_id)

    valid_statuses = [
        'Waiting for Batch',
        'Ready for Pickup',
        'Vehicle Assigned',
        'Cleanup Done',
    ]

    if operation_status in valid_statuses:
        complaint.operation_status = operation_status

        if operation_status == 'Vehicle Assigned':
            complaint.status = 'In Progress'

            if not complaint.in_progress_at:
                complaint.in_progress_at = timezone.now()

        if operation_status == 'Cleanup Done':
            complaint.status = 'Resolved'

            if not complaint.resolved_at:
                complaint.resolved_at = timezone.now()

        complaint.save()

    return redirect('dashboard')
