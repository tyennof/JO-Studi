import uuid
from io import BytesIO

import qrcode
from django.core.files.base import ContentFile
from django.db import models

from accounts.models import CustomUser
from event_mgmt.models import Event


class Eticket(models.Model):
    # Le Ebillet est lié à un seul utilisateur
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    # Le Ebillet est lié à un seul événement
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    # Offre (Nombre de place)
    offer = models.IntegerField()
    # Clé de sécurité unique du billet
    ticket_id = models.UUIDField(default=uuid.uuid4, editable=False)
    # Image pour le scan lors du contrôle
    qr_code = models.ImageField(upload_to='qr_code', blank=True, null=True)

    def __str__(self):
        return f"{self.event}"

    def qr_code_maker(self):
        data = [self.user.email, str(self.ticket_id), self.event.eventName, str(self.offer)]
        qr_img = qrcode.make(data)
        byte_arr = BytesIO()
        qr_img.save(byte_arr, format='PNG')
        byte_arr.seek(0)
        return byte_arr

    def save(self, *args, **kwargs):
        if not self.pk:  # only generate QR code for new records
            temp = self.qr_code_maker()
            self.qr_code.save(f"{self.ticket_id}.png", ContentFile(temp.read()), save=False)
        super().save(*args, **kwargs)





