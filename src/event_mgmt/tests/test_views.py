from django.test import TestCase
from django.urls import reverse

from accounts.models import CustomUser
from event_mgmt.models import Event


class EventTest(TestCase):
    def setUp(self):
        self.event = Event.objects.create(
            eventName="EventNameTest",
        )

    def test_events_are_shown_on_index_event_page(self):
        response = self.client.get(reverse("index-event-mgmt"))

        # Vérification si retour de requête est égal à 200 ( donc retour OK )
        self.assertEqual(response.status_code, 200)
        # Vérification si le nom de l'événement est bien affiché sur la page des événements
        self.assertIn(self.event.eventName, str(response.content))
        # Vérification si l'image de l'événement est bien affichée sur la page des événements
        self.assertIn(self.event.eventpic_url(), str(response.content))

    def text_connexion_link_shown_when_user_not_connected(self):
        response = self.client.get(reverse('accueil-site'))

        # Vérification si retour de requête est égal à 200 ( donc retour OK )
        self.assertEqual(response.status_code, 200)
        # Vérification si affichage de "connexion"
        self.assertIn("Connexion", str(response.content))

    def test_redirect_when_anonymous_user_access_cart_view(self):
        response = self.client.get(reverse("cart"))

        # Vérification si redirection
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, f"{reverse("login")}?next={reverse("cart")}", status_code=302)


class EventMgmtLoggedInTest(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email="test@test.fr",
            first_name="prenom",
            last_name="nom",
            password="12345678"
        )

    def test_valid_login(self):
        data = {'email': 'test@test.fr', 'password': '12345678'}
        response = self.client.post(reverse('login'), data=data)
        self.assertEqual(response.status_code, 302)
        response = self.client.get(reverse('accueil-site'))
        self.assertIn("Mon profil", str(response.content))

    def test_invalid_login(self):
        data = {'email': 'test@test.fr', 'password': '1234'}
        response = self.client.post(reverse('login'), data=data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/login.html')

    def test_profile_change(self):
        self.client.login(email="test@test.fr", password="12345678")

        url = reverse('profile', kwargs={'pk': self.user.pk})

        # Données à mettre à jour
        update_data = {
            'first_name': 'prenom',  # on renvoie le prénom existant
            'last_name': 'new_name'  # nouveau nom de famille
        }

        # Envoyer une requête POST à la vue
        response = self.client.post(url, update_data)

        # Vérifie si redirection a bien eu lieu page d'accueil après màj
        self.assertRedirects(response, reverse('accueil-site'))

        # Récupére utilisateur màj
        self.user.refresh_from_db()

        # Vérifier nom de famille a bien été mis à jour
        self.assertEqual(self.user.last_name, 'new_name')

        # Vous pouvez également tester si le prénom est inchangé
        self.assertEqual(self.user.first_name, 'prenom')


