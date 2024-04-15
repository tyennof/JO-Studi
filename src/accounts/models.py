import uuid

import stripe
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.shortcuts import get_object_or_404

from iso3166 import countries

from OGticketing import settings
from event_mgmt.models import Event, Cart, Order

stripe.api_key = settings.STRIPE_API_KEY


# Création nouvelle classe de gestion user & superuser (car utilisation d'email pour le login et plus username)
class CustomUserManager(BaseUserManager):
    def create_user(self, email, password, **kwargs):
        if not email:
            raise ValueError("Adresse email requise")

        email = self.normalize_email(email)
        user = self.model(email=email, **kwargs)
        # Utilsation de la méthode "set_password" pour que le passage du mdp soit encrypté
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password, **kwargs):
        kwargs["is_staff"] = True
        kwargs["is_superuser"] = True
        kwargs["is_active"] = True

        return self.create_user(email=email, password=password, **kwargs)


class CustomUser(AbstractUser):
    # Annulation du champ "username" (pour en utiliser un autre)
    username = None
    # Remplacement du champ (déjà existant dans le modèle) + attribut obligatoire et unique
    email = models.EmailField(max_length=240, unique=True)
    # Identifiant pour relier l'utilisateur à son compte sur Stripe
    stripe_id = models.CharField(max_length=90, blank=True)
    # identifiant unique d'utilisateur (clé secrète)
    cuid = models.UUIDField(default=uuid.uuid4, editable=False)
    # C'est ce champ qui sera utilisé pour la connexion
    USERNAME_FIELD = "email"
    # Liste des champs qui sont obligatoires pour la création d'un compte ( USERNAME_FIELD requis par défaut)
    REQUIRED_FIELDS = []
    # Écrasement de la variable "objects" par défaut pour en recréer une perso
    objects = CustomUserManager()

    def add_to_cart(self, slug):
        # Récupération de l'événement s'il existe
        event = get_object_or_404(Event, eventSlug=slug)
        # _ : convention de nommage pour une variable qu'on ne va pas utiliser par la suite (objet créé ou non)
        cart, _ = Cart.objects.get_or_create(user=self)
        order, created = Order.objects.get_or_create(user=self, ordered=False, event=event)

        if created:
            cart.orders.add(order)
            cart.save()
        else:
            order.quantity = 1
            order.save()

        return cart


ADDRESS_FORMAT = """
{name}
{address_1}
{address_2}
{city}, {zip_code}
{country}
"""


class ShippingAddress(models.Model):
    # Plusieurs adresses (en cas de livraison) rattachées à un utilisateur
    # related_name : évite d'utiliser un mot plus complexe à utiliser ( Ex : shippingaddress_set )
    user: CustomUser = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="addresses")
    # Nom de l'addresse (Ex : Travail, Domicile, etc)
    name = models.CharField(max_length=240)
    # help_text : message affiché dans le formulaire pour l'aide au remplissage du champ
    address_1 = models.CharField(max_length=1024, help_text="Adresse de voirie et N° de rue.")
    address_2 = models.CharField(max_length=1024, help_text="Bâtiment, étage, lieu-dit, ...", blank=True)
    city = models.CharField(max_length=1024)
    zip_code = models.CharField(max_length=32)
    country = models.CharField(max_length=2, choices=[(c.alpha2.lower(), c.name) for c in countries])
    default = models.BooleanField(default=False)

    def __str__(self):
        # Utilisation du unpacking  (**self) pour éviter de taper chaque champ de l'adresse
        # Clés : attributs des instances / Valeurs : valeurs de ces attributs
        # Méthode pour récupérer le bon nom d'affichage du pays (France au lieu de fr par ex)
        # On fait copie de l'instance sinon on modifie les attributs
        data = self.__dict__.copy()
        data.update(country=self.get_country_display().upper())
        # strip("\n") : enlève le \n au début et à la fin sinon ce sera intermprété en HTML
        return ADDRESS_FORMAT.format(**data).strip("\n")

    # Fonction créee pour être DRY par rapport à la fonction set_default
    def as_dict(self):
        return {
            "city": self.city,
            "country": self.country,
            "line1": self.address_1,
            "line2": self.address_2,
            "postal_code": self.zip_code
        }

    # Pour indiquer quelle adresse doit être mise par défaut
    def set_default(self):
        # Vérification si utilisateur est renseigné dans Stripe
        if not self.user.stripe_id:
            raise ValueError(f"User {self.user.email} doesn't have a stripe Customer ID.")

        # Récupération de toutes les adresses qu'on passe toutes à False pour n'en mettre qu'une seule à True
        self.user.addresses.update(default=False)
        self.default = True
        self.save()

        stripe.Customer.modify(
            self.user.stripe_id,
            shipping={"name": self.name,
                      "address": self.as_dict()},
            address=self.as_dict()
        )



