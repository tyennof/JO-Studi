from django.contrib.messages import get_messages
from django.core import mail
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from accounts.forms import ContactForm
from accounts.models import CustomUser
from accounts.verification.email_verification_token_generator import email_verification_token


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


User = get_user_model()


class ContactViewTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(email='user@example.com', password='testpassword')
        self.contact_url = reverse('contact')

    def test_contact_view_with_authenticated_user_get_request(self):
        self.client.login(email='user@example.com', password='testpassword')
        response = self.client.get(self.contact_url)
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.context['form'], ContactForm)
        self.assertEqual(response.context['form'].initial['email'], self.user.email)

    def test_contact_view_with_unauthenticated_user_get_request(self):
        response = self.client.get(self.contact_url)
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.context['form'], ContactForm)
        self.assertNotIn('email', response.context['form'].initial)

    def test_contact_form_post_with_valid_data(self):
        self.client.login(email='user@example.com', password='testpassword')
        form_data = {
            'email': 'user@example.com',
            'subject': 'Test Subject',
            'text': 'Test message'
        }
        response = self.client.post(self.contact_url, form_data)
        self.assertEqual(len(mail.outbox), 2)  # 2 messages devraient être envoyés
        self.assertRedirects(response, reverse('contact'))

        # Vérification si les messages sont ajoutés dans la session User
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]),
                         'Le message a été envoyé. Si vous ne recevez pas l\'email de confirmation,'
                         ' veuillez vérifier vos spams ou renvoyer votre message en vérifiant bien l\'email'
                         ' renseigné s\'il vous plaît.')

    def test_contact_form_post_with_invalid_data(self):
        self.client.login(email='user@example.com', password='testpassword')
        form_data = {
            'email': 'user',  # Mail invalide
            'subject': '',
            'text': 'Test message'
        }
        response = self.client.post(self.contact_url, form_data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['form'].is_valid())
        self.assertEqual(len(mail.outbox), 0)


class UserActivationTestCase(TestCase):
    def setUp(self):
        # Créer un utilisateur mais ne pas l'activer
        self.user = CustomUser.objects.create_user(email="test@example.com", password="testpassword123")
        self.user.is_active = False
        self.user.save()

        # Encoder l'ID de l'utilisateur et générer un token
        self.uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        self.token = email_verification_token.make_token(self.user)

    def test_activate_success(self):
        # Accéder à la vue avec le bon UID et token
        response = self.client.get(reverse('activate', kwargs={'uidb64': self.uid, 'token': self.token}))
        self.user.refresh_from_db()

        # Vérifier que l'utilisateur est activé
        self.assertTrue(self.user.is_active)
        # Vérifier la redirection vers la page d'accueil
        self.assertRedirects(response, reverse('accueil-site'))
        # Récupérer les messages à partir de la réponse
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), "Votre compte est désormais actif, vous pouvez vous connecter")

    def test_activate_failure(self):
        # Accéder à la vue avec un mauvais token
        response = self.client.get(reverse('activate', kwargs={'uidb64': self.uid, 'token': 'wrong-token'}))
        self.user.refresh_from_db()

        # Vérifier que l'utilisateur n'est pas activé
        self.assertFalse(self.user.is_active)
        # Vérifier la redirection vers la page d'accueil
        self.assertRedirects(response, reverse('accueil-site'))
        # Vérifier le message d'erreur
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), "Vous pouvez nous contacter par email, nous résoudrons le problème")
