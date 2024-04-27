import json

from django.contrib.auth import get_user_model
from django.forms import modelformset_factory, BaseModelFormSet
from django.test import TestCase
from django.urls import reverse

from accounts.models import CustomUser, ShippingAddress
from eticketing.models import Eticket
from event_mgmt.forms import OrderForm
from event_mgmt.models import Event, Cart, Order
from event_mgmt.views import complete_order, save_shipping_address


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


class DeleteCartViewTest(TestCase):

    def setUp(self):
        # Création d'un utilisateur
        self.user = User.objects.create_user(email='test@example.com', password='password')

        # Connexion de l'utilisateur
        self.client.login(email='test@example.com', password='password')

        # Création d'un évènement pour les commandes
        self.event = Event.objects.create(eventName="Event Test")

        # Création d'un panier pour l'utilisateur
        self.cart = Cart.objects.create(user=self.user)

        # Ajout d'une commande au panier
        self.order = Order.objects.create(user=self.user, event=self.event, quantity=2)
        self.cart.orders.add(self.order)

    def test_delete_cart(self):
        # Vérification si panier existe avant la requête de suppression
        self.assertIsNotNone(Cart.objects.filter(user=self.user).first())

        # Faire une requête POST pour simuler la suppression
        response = self.client.post(reverse('delete-cart'))

        # Vérifier que le panier a été supprimé
        self.assertIsNone(Cart.objects.filter(user=self.user).first())

        # Vérifier que la commande associée a également été supprimée (selon la logique de votre modèle)
        self.assertEqual(Order.objects.filter(user=self.user).count(), 0)

        # Vérifier la redirection après la suppression
        self.assertRedirects(response, reverse('index-event-mgmt'))


class CartViewTestCase(TestCase):
    def setUp(self):
        # Création d'un utilisateur
        self.user = User.objects.create_user(email="user@example.com", password="password")

        # Création d'un événement
        self.event = Event.objects.create(
            eventName="Concert",
            eventDateHour="2024-05-01 20:00:00",
            eventSeatAvailable=100,
            eventPlace="Concert Hall",
            eventDescription="A great concert."
        )

        # Connexion de l'utilisateur
        self.client.login(email="user@example.com", password="password")

    def test_add_to_cart(self):
        # Récupération du slug de l'événement créé
        slug = self.event.eventSlug

        # Exécution de la vue add_to_cart
        response = self.client.get(reverse("add-to-cart", kwargs={"slug": slug}))

        # Vérification que l'utilisateur est redirigé vers la page de détail de l'événement
        self.assertRedirects(response, reverse("event-detail", kwargs={"slug": slug}))

        # Vérification que l'ordre a été créé pour cet utilisateur et cet événement
        order_exists = Order.objects.filter(user=self.user, event=self.event).exists()
        self.assertTrue(order_exists)


class CheckoutSuccessViewTests(TestCase):

    def test_checkout_success_uses_correct_template(self):

        response = self.client.get(reverse('checkout-success'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'event_mgmt/success.html')


class CompleteOrderTestCase(TestCase):
    def setUp(self):
        # Création de l'utilisateur et de son panier
        self.user = CustomUser.objects.create(email="user@example.com", password="password")
        self.cart = Cart.objects.create(user=self.user)

        # Création de l'événement
        self.event = Event.objects.create(eventName="Concert", eventSeatAvailable=100)

        # Ajout d'une commande au panier
        self.order = Order.objects.create(user=self.user, event=self.event, quantity=2)
        self.cart.orders.add(self.order)

    def test_complete_order(self):
        # Données simulées pour le processus de commande
        data = {'customer': 'stripe_customer_id'}

        # Exécution de la fonction de vue
        response = complete_order(data, self.user)

        # Vérifications HTTP et d'état des objets
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.event.refresh_from_db()

        # Vérifier que l'identifiant stripe a été mis à jour
        self.assertEqual(self.user.stripe_id, 'stripe_customer_id')

        # Vérifier que les sièges disponibles de l'événement ont été déduits
        self.assertEqual(self.event.eventSeatAvailable, 98)

        # Vérifier que les tickets et les emails sont correctement créés et envoyés
        self.assertEqual(Eticket.objects.count(), 1)
        eticket = Eticket.objects.first()
        self.assertEqual(eticket.user, self.user)
        self.assertEqual(eticket.event, self.event)
        self.assertEqual(eticket.offer, 2)

        # Vérifier que le panier est vide et l'utilisateur n'a plus de panier
        self.assertFalse(Cart.objects.filter(user=self.user).exists())


class ShippingAddressTest(TestCase):

    def setUp(self):
        self.user = CustomUser.objects.create(email='test@example.com', password='testpassword123')

    def test_save_shipping_address_success(self):
        data = {
            "shipping_details": {
                "address": {
                    "city": "Paris",
                    "country": "FR",
                    "line1": "123 Rue de Exemple",
                    "line2": "Appartement 1",
                    "postal_code": "75001"
                },
                "name": "John Doe"
            }
        }
        response = save_shipping_address(data, self.user)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(ShippingAddress.objects.exists())

    def test_save_shipping_address_missing_field(self):
        data = {
            "shipping_details": {
                "address": {
                    "city": "Paris",
                    # Missing country field
                    "line1": "123 Rue de Exemple",
                    "line2": "Appartement 1",
                    "postal_code": "75001"
                },
                "name": "John Doe"
            }
        }
        response = save_shipping_address(data, self.user)
        self.assertEqual(response.status_code, 400)

    def test_save_shipping_address_invalid_country_code(self):
        data = {
            "shipping_details": {
                "address": {
                    "city": "Paris",
                    "country": "XYZ",  # Invalid country code
                    "line1": "123 Rue de Exemple",
                    "line2": "",
                    "postal_code": "75001"
                },
                "name": "John Doe"
            }
        }
        response = save_shipping_address(data, self.user)
        # Checking for valid/invalid country code can be handled in the view or model layer
        self.assertEqual(response.status_code, 200)

    def tearDown(self):
        self.user.delete()












