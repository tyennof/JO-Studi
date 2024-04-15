from django.core.mail import EmailMessage
from django.conf import settings


def send_eticket_email(eticket):
    subject = "Votre e-billet pour l'événement"
    message = (f"Bonjour {eticket.user.first_name},\n\n"
               f"Nous vous confirmons votre réservation pour l'{eticket.event.eventName}.\n"
               f"Celle-ci se déroulera le {eticket.event.eventDateHour} à {eticket.event.eventPlace}.\n"
               f"Votre offre comprend {eticket.offer} place(s).\n"
               f"Vous trouverez en pièce jointe le QR Code à présenter lors de votre passage du contrôle.\n"
               f"Nous vous souhaitons une bonne journée.\n\n"
               f"La Billeterie des Jeux Olympiques de Paris 2024.")
    email_from = settings.EMAIL_HOST_USER
    recipient_list = [eticket.user.email]
    email = EmailMessage(subject, message, email_from, recipient_list)

    # Chemin du fichier QR Code
    qr_code_path = eticket.qr_code.path

    # Ajouter le fichier QR Code comme pièce jointe
    email.attach_file(qr_code_path)

    # Envoi de l'e-mail
    email.send()
