from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import CustomUser
from eticketing.models import Eticket
from event_mgmt.models import Event


class TicketViewTest(TestCase):
    def setUp(self):
        # Créer un utilisateur
        self.user = CustomUser.objects.create(email='testuser@example.com')
        self.user.set_password('password123')
        self.user.save()

        # Créer un événement
        self.event = Event.objects.create(
            eventName='Concert de Jazz',
            eventDateHour=timezone.now(),
            eventSeatAvailable=100,
            eventPlace='Salle de Concert',
            eventDescription='Un super concert de jazz!'
        )

        # Créer un billet pour l'utilisateur
        self.eticket = Eticket.objects.create(
            user=self.user,
            event=self.event,
            offer=1
        )

    def test_tickets_view(self):
        # Connecter l'utilisateur
        self.client.login(email='testuser@example.com', password='password123')

        # Accéder à la vue
        response = self.client.get(reverse('tickets'))

        # Vérifier que la réponse est correcte
        self.assertEqual(response.status_code, 200)
        self.assertContains(response,
                            'Concert de Jazz')  # Vérifiez que le nom de l'événement est présent dans la réponse
        self.assertTemplateUsed(response, 'eticketing/tickets.html')

        # Vérifier que le contexte contient les billets de l'utilisateur
        tickets_in_context = response.context['tickets']
        self.assertEqual(len(tickets_in_context), 1)
        self.assertEqual(tickets_in_context[0], self.eticket)
