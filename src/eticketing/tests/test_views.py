from io import BytesIO
from PyPDF2 import PdfReader
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.utils.timezone import now

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


class SalesByOfferViewTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        # Création d'un utilisateur pour les tickets
        user = get_user_model().objects.create_user(email="test@test.fr", password='12345678')

        # Création d'événements
        event1 = Event.objects.create(
            eventName='breaking',
            eventDateHour=now(),
            eventSeatAvailable=100,
            eventPlace='eiffel'
        )

        event2 = Event.objects.create(
            eventName='foot',
            eventDateHour=now(),
            eventSeatAvailable=150,
            eventPlace='stade de france'
        )

        # Création de tickets pour les événements
        Eticket.objects.create(user=user, event=event1, offer=1)
        Eticket.objects.create(user=user, event=event1, offer=1)
        Eticket.objects.create(user=user, event=event1, offer=2)
        Eticket.objects.create(user=user, event=event2, offer=1)

    def test_view_url_exists_at_desired_location(self):
        response = self.client.get('/ventes_par_offre/')
        self.assertEqual(response.status_code, 200)

    def test_view_url_accessible_by_name(self):
        response = self.client.get(reverse('ventes-par-offre'))
        self.assertEqual(response.status_code, 200)

    def test_view_uses_correct_template(self):
        response = self.client.get(reverse('ventes-par-offre'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'eticketing/vue_vente.html')

    def test_list_all_events(self):
        response = self.client.get(reverse('ventes-par-offre'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['event_sales_data']), 2)
        # Vérif si total des ventes est correct pour les offres
        event_sales_data = response.context['event_sales_data']
        self.assertEqual(event_sales_data[0]['offers'][0]['total'], 2)  # pour l'offre 1 de event1
        self.assertEqual(event_sales_data[0]['offers'][1]['total'], 1)  # pour l'offre 2 de event1


class GenerateSalesPdfViewTests(TestCase):
    def setUp(self):
        # Utiliser le modèle utilisateur personnalisé
        User = get_user_model()

        # Créer un utilisateur administrateur
        self.admin_user = User.objects.create_superuser(email='admin@example.com', password='password')
        self.client.login(email='admin@example.com', password='password')

        # Créer un utilisateur régulier pour les tickets
        self.user = User.objects.create_user(email='user@example.com', password='password')

        # Créer des événements
        self.event1 = Event.objects.create(eventName='Event 1')
        self.event2 = Event.objects.create(eventName='Event 2')

        # Créer des tickets pour les événements
        Eticket.objects.create(event=self.event1, offer=1, user=self.user)
        Eticket.objects.create(event=self.event1, offer=2, user=self.user)
        Eticket.objects.create(event=self.event2, offer=4, user=self.user)

    def test_generate_sales_pdf_access(self):
        response = self.client.get(reverse('generate_sales_pdf'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')

    def test_generate_sales_pdf_data(self):
        response = self.client.get(reverse('generate_sales_pdf'))

        # Vérifier que le PDF est bien généré
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')

        # Extraire le contenu du PDF pour vérifier les données
        pdf = PdfReader(BytesIO(response.content))
        page = pdf.pages[0]
        text = page.extract_text()

        # Vérifier la présence des données correctes
        self.assertIn("Rapport de ventes par offre pour la billetterie des J.O.", text)
        self.assertIn("Solo", text)
        self.assertIn("Duo", text)
        self.assertIn("Familiale", text)
        self.assertIn("Nombre total de ventes", text)
        self.assertIn("Revenu total", text)

        # Vérifier que les nombres de ventes et revenus sont corrects
        self.assertIn("1", text)  # Pour l'offre Solo
        self.assertIn("1", text)  # Pour l'offre Duo
        self.assertIn("1", text)  # Pour l'offre Familiale
        self.assertIn("50", text)  # Revenu pour l'offre Solo
        self.assertIn("80", text)  # Revenu pour l'offre Duo
        self.assertIn("150", text)  # Revenu pour l'offre Familiale