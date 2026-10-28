from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase


class EmailRegistrationTests(APITestCase):
    def setUp(self):
        self.url = reverse('register')
        self.registration_data = {
            'username': 'new user',
            'email': 'newuser@example.com',
            'password': 'secret123',
            'password_confirm': 'secret123',
        }

    def test_registers_with_email_and_returns_jwt_tokens(self):
        response = self.client.post(self.url, self.registration_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['access'])
        self.assertTrue(response.data['refresh'])
        user = get_user_model().objects.get(username='new user')
        self.assertEqual(user.email, 'newuser@example.com')
        self.assertFalse(user.phone)
        self.assertFalse(user.first_name)
        self.assertFalse(user.last_name)

        login_response = self.client.post(reverse('login'), {
            'username': 'new user',
            'password': 'secret123',
        }, format='json')
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)

        email_login_response = self.client.post(reverse('login'), {
            'username': 'NEWUSER@example.com',
            'password': 'secret123',
        }, format='json')
        self.assertEqual(email_login_response.status_code, status.HTTP_200_OK)

    def test_rejects_an_email_that_is_already_registered(self):
        get_user_model().objects.create_user(
            username='existing',
            email='newuser@example.com',
            password='secret123',
        )

        response = self.client.post(self.url, self.registration_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], '该邮箱已被注册')

    def test_rejects_registration_without_email(self):
        data = {**self.registration_data, 'email': ''}

        response = self.client.post(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data['details'])

    def test_login_validation_prompts_for_username_or_email(self):
        response = self.client.post(reverse('login'), {
            'username': '',
            'password': '',
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error_code'], 'credentials_required')
        self.assertEqual(response.data['error'], '请输入用户名或邮箱和密码')


class UserProfileUpdateTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='profile user',
            email='profile@example.com',
            password='secret123',
        )
        self.client.force_authenticate(self.user)
        self.url = reverse('profile')

    def test_updates_username_and_keeps_email_unchanged(self):
        response = self.client.patch(self.url, {
            'username': 'updated profile',
            'email': 'changed@example.com',
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, 'updated profile')
        self.assertEqual(self.user.email, 'profile@example.com')
        self.assertEqual(response.data['email'], 'profile@example.com')

    def test_rejects_username_already_in_use(self):
        get_user_model().objects.create_user(
            username='taken name',
            email='taken@example.com',
            password='secret123',
        )

        response = self.client.patch(self.url, {'username': 'taken name'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('username', response.data)
