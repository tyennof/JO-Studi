from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from io import BytesIO
import datetime

from accounts.models import CustomUser
from eticketing.function.order_confirmation_email import send_eticket_email
from eticketing.models import Eticket
from event_mgmt.models import Event


class SendETicketEmailTest(TestCase):

    def setUp(self):
        # Création de l'utilisateur
        self.user = CustomUser.objects.create(email='steve.paris2024@gmail.com', password='password123')

        # Création de l'événement
        self.event = Event.objects.create(
            eventName="Aviron",
            eventDateHour=datetime.datetime.now(),
            eventPlace="Chelles"
        )

        # Création du billet électronique
        self.eticket = Eticket.objects.create(
            user=self.user,
            event=self.event,
            offer=1
        )

        # Simulation d'un fichier QR Code
        qr_code_file = BytesIO(b'Test QR Code')  # Simuler un contenu de fichier QR Code
        qr_code_file.name = 'test_qr.png'
        self.eticket.qr_code = SimpleUploadedFile(name='test_qr.png', content=qr_code_file.getvalue(),
                                                  content_type='image/png')
        self.eticket.save()

    def test_send_eticket_email(self):
        # Appel de la fonction à tester
        send_eticket_email(self.eticket)


