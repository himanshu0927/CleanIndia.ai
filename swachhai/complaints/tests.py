import io
import tempfile

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import TestCase, override_settings
from PIL import Image

from .models import Complaint, UserProfile


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
