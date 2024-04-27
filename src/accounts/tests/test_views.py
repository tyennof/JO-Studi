from email.headerregistry import Address
from multiprocessing.connection import Client

from django.contrib.auth.mixins import LoginRequiredMixin
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User


class LoginUserViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Création d'un utilisateur pour les tests de connexion
        cls.user = get_user_model().objects.create_user(email='test@example.com', password='testpass123')

    def test_login_view_status_code(self):
        # Test de la réponse GET
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)

    def test_successful_login(self):
        # Test de la connexion avec des identifiants valides
        response = self.client.post(reverse('login'), {
            'email': 'test@example.com',
            'password': 'testpass123'
        }, follow=True)
        self.assertTrue(response.context['user'].is_authenticated)
        self.assertRedirects(response, reverse('accueil-site'))

    def test_unsuccessful_login(self):
        # Test de la connexion avec des identifiants invalides
        response = self.client.post(reverse('login'), {
            'email': 'test@example.com',
            'password': 'wrongpassword'
        })
        self.assertFalse(response.context['user'].is_authenticated)
        self.assertEqual(response.status_code, 200)

    def test_login_template_used(self):
        # Vérification que le bon template est utilisé
        response = self.client.get(reverse('login'))
        self.assertTemplateUsed(response, 'accounts/login.html')


class LogoutUserViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Création d'un utilisateur pour les tests de déconnexion
        cls.user = get_user_model().objects.create_user(email='test@example.com', password='testpass123')

    def test_logout(self):
        # Connexion de l'utilisateur
        self.client.login(email='test@example.com', password='testpass123')

        # Vérification que l'utilisateur est connecté
        user = get_user_model().objects.get(email='test@example.com')
        self.assertTrue(user.is_authenticated)

        # Déconnexion de l'utilisateur
        response = self.client.get(reverse('logout'), follow=True)

        # Vérification que l'utilisateur est déconnecté
        self.assertFalse(response.context['user'].is_authenticated)

        # Vérification que la redirection a bien été effectuée vers la page d'accueil
        self.assertRedirects(response, reverse('accueil-site'))

    def test_logout_template_used(self):
        # Connexion de l'utilisateur
        self.client.login(email='test@example.com', password='testpass123')

        # Déconnexion de l'utilisateur
        response = self.client.get(reverse('logout'), follow=True)

        # Vérification que le bon template est utilisé après la déconnexion
        self.assertTemplateUsed(response, 'event_mgmt/accueil_site.html')


class UpdateProfileTestCase(TestCase):
    def setUp(self):

        self.user = get_user_model().objects.create_user(
            email='test@example.com',
            password='testpassword',
            last_name='Doe',
            first_name='John'
        )
        self.client.login(email='test@example.com', password='testpassword')

    def test_update_profile_view(self):

        update_url = reverse('profile', kwargs={'pk': self.user.pk})

        updated_data = {
            'last_name': 'Smith',
            'first_name': 'Jane'
        }

        response = self.client.post(update_url, updated_data)

        self.user.refresh_from_db()

        self.assertEqual(self.user.last_name, 'Smith')
        self.assertEqual(self.user.first_name, 'Jane')

        self.assertRedirects(response, reverse('profile', kwargs={'pk': self.user.pk}))


class SignupViewTests(TestCase):
    def setUp(self):
        self.url = reverse('signup')
        self.user_model = get_user_model()

    def test_get_signup_form(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/signup.html')
        self.assertIn('form', response.context)

    def test_successful_signup_redirects(self):
        response = self.client.post(self.url, {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john@example.com',
            'password1': 'somepassword123',
            'password2': 'somepassword123'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(self.user_model.objects.filter(email='john@example.com').exists())
        self.assertRedirects(response, reverse('accueil-site'))

    def test_signup_with_invalid_data(self):
        response = self.client.post(self.url, {
            'first_name': 'Jane',
            'last_name': 'Doe',
            'email': 'jane@example.com',
            'password1': 'somepassword123',
            'password2': 'wrongpassword'
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(self.user_model.objects.filter(email='jane@example.com').exists())
        self.assertIn('form', response.context)
        self.assertFalse(response.context['form'].is_valid())
        self.assertIn('password2', response.context['form'].errors)








