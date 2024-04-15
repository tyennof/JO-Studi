from django.db import models
from django.templatetags.static import static
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify

from OGticketing.settings import AUTH_USER_MODEL


class Event(models.Model):
    # Nom de l'événement ( Obligation de mettre un "max_length" pour ce champ )
    eventName = models.CharField(max_length=128)
    # Slug de l'événement (permet d'obtenir une string utile à création url permettant accès à page événement)
    eventSlug = models.SlugField(max_length=128, blank=True)
    # Date et heure de l'événement
    eventDateHour = models.DateTimeField(blank=True, null=True)
    # Nombre de places disponibles
    eventSeatAvailable = models.IntegerField(blank=True, null=True)
    # Lieu de l'événement ( Obligation de mettre un "max_length" pour ce champ )
    eventPlace = models.CharField(max_length=128, blank=True)
    # Image d'illustration de l'événement ( si champ vide, mise de la valeur "null" dans BDD )
    eventPic = models.ImageField(upload_to="event_pic", blank=True, null=True)
    # Description de l'événement
    eventDescription = models.TextField(blank=True)
    # Permet de faire le lien entre nos événements et ceux enregistrés sur Stripe
    stripe_id = models.CharField(max_length=90, blank=True)

    # Permet de modifier l'affichage dans interface Admin Django ( "Event object (x)" par défaut)
    def __str__(self):
        return f"{self.eventName}"

    def get_absolute_url(self):
        return reverse('event-detail', kwargs= {"slug": self.eventSlug})

    # Rempli automatiquement le champ eventSlug
    def save(self, *args, **kwargs):
        self.eventSlug = self.eventSlug or slugify(self.eventName)
        super().save(*args, **kwargs)

    def eventpic_url(self):
        return self.eventPic.url if self.eventPic else static("picture/default_event.jpg")


class Order(models.Model):
    # Relation "plusieurs à un" (plusieurs produits reliés à un utilisateur)
    user = models.ForeignKey(AUTH_USER_MODEL, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    ordered = models.BooleanField(default=False)
    ordered_date = models.DateTimeField(blank=True, null=True)

    # Permet de modifier l'affichage dans interface Admin Django
    def __str__(self):
        return f"{self.event.eventName} ({self.quantity})"


class Cart(models.Model):
    # 1 seul panier ne peut être rattaché qu'à un seul utilisateur
    user = models.OneToOneField(AUTH_USER_MODEL, on_delete=models.CASCADE)
    orders = models.ManyToManyField(Order)

    # Permet de modifier l'affichage dans interface Admin Django
    def __str__(self):
        return self.user.email

    def order_ok(self):
        for order in self.orders.all():
            order.ordered = True
            order.ordered_date = timezone.now()
            order.save()

        self.orders.clear()
        self.delete()

    def delete(self, *args, **kwargs):
        orders = self.orders.all()

        for order in orders:
            order.delete()
        super().delete(*args, **kwargs)






