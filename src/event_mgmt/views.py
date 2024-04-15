import stripe
from django.contrib.auth.decorators import login_required
from django.forms import modelformset_factory
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

from django.conf import settings

from OGticketing.settings import env
from accounts.models import CustomUser, ShippingAddress
from eticketing.function.order_confirmation_email import send_eticket_email
from eticketing.models import Eticket
from event_mgmt.forms import OrderForm
from event_mgmt.models import Event, Cart, Order


stripe.api_key = settings.STRIPE_API_KEY


# Page qui présente tous les événements
def index_event_mgmt(request):
    events = Event.objects.all()

    return render(request, 'event_mgmt/index_event_mgmt.html', context={"events": events})


def accueil_site(request):
    return render(request, 'event_mgmt/accueil_site.html')


def mention(request):
    return render(request, 'event_mgmt/mention.html')


def cgv(request):
    return render(request, 'event_mgmt/cgv.html')


def event_detail(request, slug):
    event = get_object_or_404(Event, eventSlug=slug)
    return render(request, 'event_mgmt/event_detail.html', context={"event": event})


def add_to_cart(request, slug):
    # Création de cette variable à des fins de réutilisation successive
    user: CustomUser = request.user
    # La logique se réalise dans le modèle
    user.add_to_cart(slug=slug)

    return redirect(reverse("event-detail", kwargs={"slug": slug}))


@login_required()
def cart(request):
    cart = get_object_or_404(Cart, user=request.user)
    # mdelformset_factory :permet de gérer potentiellement plusieurs formulaires sur une même page
    OrderFormSet = modelformset_factory(Order, form=OrderForm, extra=0)
    # On ne cible que le panier de l'utilisateur
    formset = OrderFormSet(queryset=Order.objects.filter(user=request.user, ordered=False))
    return render(request, 'event_mgmt/cart.html', context={"orders": cart.orders.all(), "forms": formset})


def update_quantities(request):
    OrderFormSet = modelformset_factory(Order, form=OrderForm, extra=0)
    formset = OrderFormSet(request.POST, queryset=Order.objects.filter(user=request.user))
    if formset.is_valid():
        formset.save()

    return redirect('cart')


def create_checkout_session(request):
    # Récupération du panier de l'utilisateur
    cart = request.user.cart

    # Création d'un dico à partir du parcours de toutes les commandes présentes dans le panier
    line_items = [{"price": order.event.stripe_id,
                   "quantity": order.quantity}
                  for order in cart.orders.all()]

    checkout_data = {
                    "payment_method_types": ['card'],
                    "line_items": line_items,
                    "mode": 'payment',
                    "locale": "fr",
                    "shipping_address_collection": {"allowed_countries": ["FR", "US", "CA"]},
                    "success_url": request.build_absolute_uri(reverse('checkout-success')),
                    "cancel_url": request.build_absolute_uri(reverse('cart')),
                    }

    if request.user.stripe_id:
        checkout_data["customer"] = request.user.stripe_id
    else:
        checkout_data["customer_email"] = request.user.email
        checkout_data["customer_creation"] = "always"

    # Unpacking du dictionnaire checkout_data
    session = stripe.checkout.Session.create(**checkout_data)

    return redirect(session.url, code=303)


def checkout_success(request):
    return render(request, 'event_mgmt/success.html')


def delete_cart(request):
    # Utilisation de l'opérateur Walrus ( vérification cart puis assignation de request.user.cart)
    if cart := request.user.cart:
        # la logique se retrouve directement dans la méthode delete du modele cart
        cart.delete()

    return redirect("index-event-mgmt")


# Ajout décorateur csrf pour la sécurité (étant donné que ce n'est pas un form qui est envoyé)
@csrf_exempt
def stripe_webhook(request):
    # Récupération du corps de la requête
    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']
    # Clé permettant de vérifier que la requête vient effectivement de Stripe (en tapant l'url dédiée par exemple)
    endpoint_secret = env('ENDPOINT_SECRET')
    event = None

    try:
        # Essai de construction d'un événement
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except ValueError as e:
        # Paiement invalide
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        # Signature invalide
        return HttpResponse(status=400)

    if event['type'] == 'checkout.session.completed':
        data = event['data']['object']

        try:
            user = get_object_or_404(CustomUser, email=data['customer_details']['email'])
        except KeyError:
            return HttpResponse("Invalid user email", status=404)

        complete_order(data=data, user=user)
        save_shipping_address(data=data, user=user)

        return HttpResponse(status=200)

    # Si vérification de la signature réussi
    return HttpResponse(status=200)


def complete_order(data, user):
    orders = user.cart.orders.all()
    for order in orders:
        # Création des Ebillets pour chaque commande
        eticket = Eticket.objects.create(user=user, event=order.event, offer=order.quantity)
        # Envoi mail pour le Ebillet
        send_eticket_email(eticket)
        # Déduction des places vendues du total des sièges dispo pour l'événément
        order.event.eventSeatAvailable -= order.quantity
        order.event.save()

    user.stripe_id = data['customer']
    user.cart.order_ok()
    user.save()

    return HttpResponse(status=200)


# Récupération des données renseignées dans Stripe pour les enregistrer dans notre BDD
def save_shipping_address(data, user):

    try:
        address = data["shipping_details"]["address"]
        name = data["shipping_details"]["name"]
        city = address["city"]
        country = address["country"]
        line1 = address["line1"]
        line2 = address["line2"]
        zip_code = address["postal_code"]
    except KeyError:
        return HttpResponse(status=400)

    ShippingAddress.objects.get_or_create(user=user,
                                          name=name,
                                          city=city.upper(),
                                          country=country.lower(),
                                          address_1=line1,
                                          # Si on a None pour Line2 alors on met une string vide pour éviter une erreur
                                          address_2=line2 or "",
                                          zip_code=zip_code)
    return HttpResponse(status=200)