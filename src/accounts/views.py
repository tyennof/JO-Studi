from smtplib import SMTPException

from django.contrib import messages
from django.contrib.auth import get_user_model, login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.mail import send_mail
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from django.views.generic import UpdateView

from OGticketing.settings import env
from accounts.forms import ContactForm, SignUpForm, SignInForm
from accounts.models import ShippingAddress
from accounts.verification.email_verification_token_generator import email_verification_token
from accounts.verification.registration import send_email_verification

# Récupération du modèle User nécessaire à la création d'un user dans la fonction signup
User = get_user_model()


def signup(request):
    # Vérification s'il s'agit bien d'une requête de type POST
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.save()
            try:
                send_email_verification(request, user)
            except SMTPException:
                pass
            return redirect('accueil-site')

    else:
        form = SignUpForm()

    return render(request, 'accounts/signup.html', context={"form": form})


def activate(request, uidb64, token):
    user = get_user_model()
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = user.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, user.DoesNotExist):
        user = None
    if user is not None and email_verification_token.check_token(user, token):
        user.is_active = True
        user.save()
        messages.add_message(request, messages.INFO, "Votre compte est désormait actif, vous pouvez vous connecter")
        return redirect("accueil-site")
    else:
        messages.add_message(request, messages.INFO,
                             "Vous pouvez nous contacter par email, nous résoudrons le problème")
        return redirect("accueil-site")


def login_user(request):
    if request.method == "POST":
        form = SignInForm(request.POST)
        if form.is_valid():
            email = request.POST.get("email")
            password = request.POST.get("password")
            user = authenticate(request, email=email, password=password)

            if user is not None:
                login(request, user)
                return redirect('accueil-site')
            else:
                form.add_error(None, "Email ou mot de passe incorrect.")
        else:
            form.add_error(None, "Veuillez remplir correctement le formulaire.")
    else:
        form = SignInForm()

    return render(request, 'accounts/login.html', {'form': form})


def logout_user(request):
    logout(request)
    return redirect('accueil-site')


class UpdateProfile(LoginRequiredMixin, UpdateView):
    model = get_user_model()
    template_name = "accounts/profile.html"
    fields = ["last_name", "first_name"]

    def get_success_url(self):
        return reverse_lazy('profile', kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        addresses = self.request.user.addresses.all()
        context["addresses"] = addresses
        return context


@login_required
def set_default_shipping_address(request, pk):
    address: ShippingAddress = get_object_or_404(ShippingAddress, pk=pk)
    address.set_default()
    return redirect('profile', pk=request.user.pk)


@login_required
def delete_address(request, pk):
    address = get_object_or_404(ShippingAddress, pk=pk, user=request.user)

    if address.default:
        messages.add_message(request, messages.ERROR, "Impossible de supprimer une adresse par défaut.")
    else:
        address.delete()

    return redirect('profile', pk=request.user.pk)


def contact(request):
    user = request.user

    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"]
            subject = form.cleaned_data["subject"]
            text = form.cleaned_data["text"]
            send_mail(subject=subject, message=f"De la part de {email} - {text}",
                      recipient_list=[env('EMAIL_ID')], from_email=None)
            send_mail(subject="Votre demande contact",
                      message=f"Bonjour {user.first_name if user.is_authenticated else ''},"
                              f"\n\n Nous avons bien reçu votre demande de support et nous nous "
                              f"engageons à y répondre dans les plus brefs délais.\n  Bien cordialement \n\n"
                              f" L'équipe support de la billeterie des JO 2024.",
                      from_email=None, recipient_list=[email])
            messages.add_message(request, messages.INFO,
                                 "Le message a été envoyé. Si vous ne recevez pas l'email "
                                 "de confirmation, veuillez vérifier vos spams ou renvoyer votre "
                                 "message en vérifiant bien l'email renseigné s'il vous plaît.")
            return redirect("contact")
    else:
        form = ContactForm(initial={"email": user.email}) if user.is_authenticated else ContactForm()

    return render(request, "accounts/contact.html", context={"form": form})
