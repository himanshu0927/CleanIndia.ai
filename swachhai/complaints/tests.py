import io
import tempfile
from datetime import datetime
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.utils import timezone
from PIL import Image

from .models import Complaint, UserProfile
from .views import is_service_open_now


@override_settings(AUTHORITY_SIGNUP_CODE='test-authority-code')
class SignupSessionTests(TestCase):
    def test_signup_creates_authenticated_session_for_each_role(self):
        for role, expected_url in [('user', '/'), ('authority', '/dashboard/')]:
            with self.subTest(role=role):
                self.client.logout()
                response = self.client.post(f'/{role}-signup/', {
                    'username': f'{role}_test',
                    'email': f'{role}@example.com',
                    'phone_number': '9876543210' if role == 'user' else '9876543211',
                    'password1': 'Strong-test-password-984!',
                    'password2': 'Strong-test-password-984!',
                    'authority_code': 'test-authority-code',
                })
                self.assertRedirects(response, expected_url, fetch_redirect_response=False)
                user = get_user_model().objects.get(username=f'{role}_test')
                self.assertEqual(user.is_staff, role == 'authority')
                self.assertEqual(int(self.client.session['_auth_user_id']), user.pk)
                self.assertTrue(UserProfile.objects.filter(user=user).exists())

                for identifier in (
                    user.username,
                    user.email,
                    user.profile.phone_number,
                ):
                    with self.subTest(role=role, identifier=identifier):
                        self.client.logout()
                        login_response = self.client.post(f'/{role}-login/', {
                            'username': identifier,
                            'password': 'Strong-test-password-984!',
                        })
                        self.assertRedirects(
                            login_response,
                            expected_url,
                            fetch_redirect_response=False,
                        )
                        self.assertEqual(int(self.client.session['_auth_user_id']), user.pk)

    def test_wrong_login_page_explains_account_role(self):
        user_model = get_user_model()
        authority = user_model.objects.create_user(
            username='staff_login_test',
            password='Strong-test-password-984!',
            is_staff=True,
        )
        citizen = user_model.objects.create_user(
            username='citizen_login_test',
            password='Strong-test-password-984!',
        )

        for path, user, message in (
            ('/user-login/', authority, 'Please use Authority Login'),
            ('/authority-login/', citizen, 'Only authority/staff accounts'),
        ):
            with self.subTest(path=path):
                response = self.client.post(path, {
                    'username': user.username,
                    'password': 'Strong-test-password-984!',
                })
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, message)
                self.assertNotIn('_auth_user_id', self.client.session)


@override_settings(
    SERVICE_OPEN_HOUR=0,
    SERVICE_CLOSE_HOUR=24,
    USE_REAL_AI_MODEL=False,
)
class ComplaintDashboardFlowTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.citizen = user_model.objects.create_user(
            username='citizen',
            password='Strong-test-password-984!',
        )
        self.authority = user_model.objects.create_user(
            username='authority',
            password='Strong-test-password-984!',
            is_staff=True,
        )

    def make_test_image(self):
        image = Image.new('RGB', (200, 200))
        pixels = image.load()
        for y in range(200):
            for x in range(200):
                pixels[x, y] = (35, 95, 45) if x < 100 else (220, 185, 70)

        buffer = io.BytesIO()
        image.save(buffer, format='JPEG')
        return SimpleUploadedFile(
            'live-captured-complaint.jpg',
            buffer.getvalue(),
            content_type='image/jpeg',
        )

    def test_citizen_submission_appears_on_authority_dashboard(self):
        with tempfile.TemporaryDirectory() as media_root:
            with self.settings(MEDIA_ROOT=media_root):
                self.client.force_login(self.citizen)
                response = self.client.post('/report/', {
                    'location': 'Gola',
                    'latitude': 28.0786,
                    'longitude': 80.4705,
                    'category': 'garbage',
                    'description': 'Garbage is lying beside the main road.',
                    'image': self.make_test_image(),
                    'is_live_photo': 'true',
                })

                if response.status_code != 302:
                    self.fail(response.context['form'].errors.as_text())
                self.assertEqual(response.url, '/my-complaints/')
                complaint = Complaint.objects.get()
                self.assertEqual(complaint.name, self.citizen.username)
                self.assertEqual(complaint.detected_area, 'Gola')

                self.client.force_login(self.authority)
                dashboard = self.client.get('/dashboard/')
                self.assertEqual(dashboard.status_code, 200)
                self.assertContains(dashboard, 'Garbage is lying beside the main road.')
                self.assertContains(dashboard, 'citizen')

    def test_reset_accounts_keeps_complaints_but_removes_old_owner(self):
        Complaint.objects.create(
            name=self.citizen.username,
            location='Gola',
            category='garbage',
            description='Test complaint',
            image='garbage_images/test.jpg',
        )
        call_command('reset_accounts')
        self.assertEqual(get_user_model().objects.count(), 2)

        call_command('reset_accounts', confirm=True)
        self.assertEqual(get_user_model().objects.count(), 0)
        self.assertEqual(Complaint.objects.get().name, '[deleted account]')

    @override_settings(SERVICE_OPEN_HOUR=8, SERVICE_CLOSE_HOUR=17)
    def test_service_closes_at_five_pm(self):
        for hour, minute, expected in [(16, 59, True), (17, 0, False)]:
            with self.subTest(hour=hour, minute=minute):
                local_time = timezone.make_aware(datetime(2026, 9, 12, hour, minute))
                with patch('complaints.views.timezone.localtime', return_value=local_time):
                    self.assertEqual(is_service_open_now(), expected)

    @override_settings(SERVICE_OPEN_HOUR=8, SERVICE_CLOSE_HOUR=17)
    def test_complaint_is_not_saved_after_five_pm(self):
        self.client.force_login(self.citizen)
        local_time = timezone.make_aware(datetime(2026, 9, 12, 17, 0))
        with patch('complaints.views.timezone.localtime', return_value=local_time):
            response = self.client.post('/report/', {
                'location': 'Gola',
                'latitude': 28.0786,
                'longitude': 80.4705,
                'category': 'garbage',
                'description': 'Garbage is lying beside the main road.',
                'image': self.make_test_image(),
                'is_live_photo': 'true',
            })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Service is available only between 8 AM and 5 PM')
        self.assertEqual(Complaint.objects.count(), 0)


class DashboardProfileTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.citizen = user_model.objects.create_user(
            username='citizen_profile',
            email='citizen@example.com',
            password='Strong-test-password-984!',
        )
        UserProfile.objects.create(user=self.citizen, phone_number='9876543210')
        self.authority = user_model.objects.create_user(
            username='authority_profile',
            email='authority@example.com',
            password='Strong-test-password-984!',
            is_staff=True,
        )

    def test_citizen_dashboard_shows_only_own_signup_details(self):
        self.client.force_login(self.citizen)
        response = self.client.get('/my-complaints/')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'citizen@example.com')
        self.assertContains(response, '9876543210')
        self.assertContains(response, 'Citizen')
        self.assertNotContains(response, 'authority@example.com')

    def test_authority_dashboard_handles_account_without_phone_profile(self):
        self.client.force_login(self.authority)
        response = self.client.get('/dashboard/')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'authority@example.com')
        self.assertContains(response, 'Authority')
        self.assertContains(response, 'Not provided')
        self.assertNotContains(response, 'citizen@example.com')
