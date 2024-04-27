from django.contrib.auth import get_user_model
from django.forms import modelformset_factory, BaseModelFormSet
from django.test import TestCase
from django.urls import reverse

from accounts.models import CustomUser
from event_mgmt.forms import OrderForm
from event_mgmt.models import Event, Cart, Order


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

        # Récupére utilisateur màj
        self.user.refresh_from_db()

        # Vérifier nom de famille a bien été mis à jour
        self.assertEqual(self.user.last_name, 'new_name')

        # Vous pouvez également tester si le prénom est inchangé
        self.assertEqual(self.user.first_name, 'prenom')


class EventViewTests(TestCase):
    def setUp(self):
        # Créer un événement de test dans la base de données
        self.event = Event.objects.create(
            eventName='aviron',
            eventDateHour='2023-10-05 20:00:00',
            eventSeatAvailable=100,
            eventPlace='chelles',
            eventDescription='magnifique épreuve',
        )
        # S'assurer que le slug est correctement généré
        self.event.save()

    def test_event_detail_view_success(self):
        # Créer l'URL en utilisant le slug de l'événement
        url = reverse('event-detail', args=[self.event.eventSlug])
        response = self.client.get(url)
        # Vérifier que la vue retourne un statut HTTP 200
        self.assertEqual(response.status_code, 200)
        # Vérifier que le bon template est utilisé
        self.assertTemplateUsed(response, 'event_mgmt/event_detail.html')
        # Vérifier que le contexte contient l'événement correct
        self.assertEqual(response.context['event'], self.event)

    def test_event_detail_view_not_found(self):
        # Tester avec un slug qui n'existe pas
        url = reverse('event-detail', args=['non-existent-slug'])
        response = self.client.get(url)
        # Vérifier que la vue retourne un statut HTTP 404
        self.assertEqual(response.status_code, 404)


class StaticsPagesTests(TestCase):
    def test_page_cgv_are_shown(self):
        response = self.client.get(reverse("cgv"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'event_mgmt/cgv.html')

    def test_page_mention_are_shown(self):
        response = self.client.get(reverse("mention"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'event_mgmt/mention.html')


User = get_user_model()


class CartViewTests(TestCase):
    def setUp(self):
        # Création d'un utilisateur
        self.user = User.objects.create_user(email='test@example.com', password='testpassword')
        self.client.login(email='test@example.com', password='testpassword')

        # Création d'un événement pour associer à la commande
        self.event = Event.objects.create(eventName="Concert")

        # Création d'un panier pour l'utilisateur
        self.cart = Cart.objects.create(user=self.user)

        # Création d'une commande non commandée
        self.order = Order.objects.create(user=self.user, event=self.event, quantity=2, ordered=False)
        self.cart.orders.add(self.order)

    def test_cart_view_with_authenticated_user(self):
        response = self.client.get(reverse('cart'))

        # Vérification que la vue fonctionne correctement
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'event_mgmt/cart.html')

        # Vérification des contextes
        orders_in_context = list(response.context['orders'])
        self.assertIn(self.order, orders_in_context)

        # Vérification que le formset est correctement initialisé
        forms = response.context['forms']
        self.assertIsInstance(forms, BaseModelFormSet)  # Testez si `forms` est une instance de BaseModelFormSet
        self.assertEqual(forms.queryset.count(), 1)
        self.assertEqual(forms.queryset.first(), self.order)

    def test_cart_view_with_no_order(self):
        # Suppression de toutes les commandes pour tester un panier vide
        self.order.delete()

        response = self.client.get(reverse('cart'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'event_mgmt/cart.html')

        # Le contexte devrait avoir une queryset vide pour les orders
        forms = response.context['forms']
        self.assertEqual(forms.queryset.count(), 0)


class UpdateQuantitiesViewTest(TestCase):

    def setUp(self):
        # Créer un utilisateur pour tester
        self.user = get_user_model().objects.create_user(email='test@example.com', password='password')
        self.client.login(email='test@example.com', password='password')

        # Créer un évènement pour tester
        self.event = Event.objects.create(eventName='Concert')

        # Créer des commandes pour cet utilisateur
        Order.objects.create(user=self.user, event=self.event, quantity=1)
        Order.objects.create(user=self.user, event=self.event, quantity=2)

    def test_update_quantities(self):
        # URL pour la requête POST
        url = reverse('update-quantities')

        # Création du formset pour simuler la requête POST
        OrderFormSet = modelformset_factory(Order, form=OrderForm, extra=0)
        formset_data = {
            'form-TOTAL_FORMS': '2',
            'form-INITIAL_FORMS': '2',
            'form-0-id': '1',
            'form-0-quantity': '1',
            'form-0-delete': '',
            'form-1-id': '2',
            'form-1-quantity': '1',
            'form-1-delete': 'on',
        }

        self.client.post(url, formset_data)

        # Vérifier que les quantités ont été mises à jour
        self.assertEqual(Order.objects.get(id=1).quantity, 1)

        # Vérifier que l'ordre avec delete=True est supprimé
        with self.assertRaises(Order.DoesNotExist):
            Order.objects.get(id=2)

    def tearDown(self):
        # Nettoyage après chaque test
        self.user.delete()
        self.event.delete()











