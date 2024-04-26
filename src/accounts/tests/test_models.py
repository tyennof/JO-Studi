from django.contrib.auth import get_user_model
from django.test import TestCase

from accounts.models import CustomUser, ShippingAddress
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


User = get_user_model()


class CustomUserManagerTests(TestCase):
    def test_create_user(self):
        user = User.objects.create_user(email='test@example.com', password='foo')
        self.assertEqual(user.email, 'test@example.com')
        self.assertTrue(user.check_password('foo'))
        self.assertFalse(user.is_superuser)
        self.assertFalse(user.is_staff)

    def test_create_user_no_email(self):
        with self.assertRaises(ValueError):
            User.objects.create_user(email=None, password='foo')

    def test_create_superuser(self):
        admin_user = User.objects.create_superuser(email='admin@example.com', password='foo')
        self.assertTrue(admin_user.is_superuser)
        self.assertTrue(admin_user.is_staff)
        self.assertTrue(admin_user.is_active)


class CustomUserTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='user@example.com', password='foo')

    def test_add_to_cart(self):
        event = Event.objects.create(eventName='Concert', eventSlug='concert')
        cart = self.user.add_to_cart(slug='concert')
        self.assertEqual(cart.orders.count(), 1)


class ShippingAddressTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='user@example.com', password='foo')
        self.user.stripe_id = "cus_PxYJCL0d0XrH3F"
        self.address = ShippingAddress.objects.create(
            user=self.user,
            name="Domicile",
            address_1="2 rue libre",
            city="lyon",
            zip_code="69000",
            country='fr'
        )

    def test_address_str(self):
        expected_address_str = "Domicile\n2 rue libre\n\nlyon, 69000\nFRANCE"
        self.assertEqual(str(self.address), expected_address_str)

    def test_set_default(self):
        new_address = ShippingAddress.objects.create(
            user=self.user,
            name="Work",
            address_1="123 Work St",
            city="Worktown",
            zip_code="12345",
            country='us'
        )
        new_address.set_default()
        self.assertTrue(new_address.default)
        self.assertFalse(self.address.default)
