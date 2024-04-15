from django.test import TestCase
from django.urls import reverse

from accounts.models import CustomUser
from event_mgmt.models import Event, Cart, Order


class EventTest(TestCase):
    def setUp(self):
        self.event = Event.objects.create(
            eventName="Event tesT",
        )

    def test_event_slug_is_automatically_generated(self):
        self.assertEqual(self.event.eventSlug, "event-test")

    def test_event_absolute_url(self):
        self.assertEqual(self.event.get_absolute_url(),
                         reverse('event-detail', kwargs= {"slug": self.event.eventSlug}))


class CartTest(TestCase):
    def setUp(self):
        user = CustomUser.objects.create_user(
            email="testuser@test.fr",
            password="12345678"
        )
        event = Event.objects.create(
            eventName="EventNameTest",
        )
        self.cart = Cart.objects.create(
            user=user
        )
        order = Order.objects.create(
            user=user,
            event=event
        )
        self.cart.orders.add(order)
        self.cart.save()


