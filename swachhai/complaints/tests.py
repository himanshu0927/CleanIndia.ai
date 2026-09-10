from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings

from .models import UserProfile


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
