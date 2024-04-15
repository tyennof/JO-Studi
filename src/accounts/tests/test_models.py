from django.test import TestCase

from accounts.models import CustomUser
from event_mgmt.models import Event


class UserTest(TestCase):
    def setUp(self):
        Event.objects.create(
            eventName="Event Test"
        )

        self.user: CustomUser = CustomUser.objects.create_user(
            email="test@test.fr",
            password="12345678"
        )

    def test_add_to_cart(self):
        # Ajout d'une réservation dans le panier et vérification si présence dans celui-ci
        self.user.add_to_cart(slug="event-test")
        self.assertEqual(self.user.cart.orders.count(), 1)
        self.assertEqual(self.user.cart.orders.first().event.eventSlug, "event-test")

        # Simulation d'une tentative de second ajout du même event dans le panier
        # et vérification que la quantité ne change pas
        self.user.add_to_cart(slug="event-test")
        self.assertEqual(self.user.cart.orders.count(), 1)
        self.assertEqual(self.user.cart.orders.first().quantity, 1)
