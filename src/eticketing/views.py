from io import BytesIO

import matplotlib
from django.http import HttpResponse
from django.shortcuts import render
from django.views.generic import ListView
from django.db.models import Count
from matplotlib import pyplot as plt
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Table, TableStyle

matplotlib.use('Agg')
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

from eticketing.models import Eticket
from event_mgmt.models import Event


def tickets(request):
    # Récupération dans une variable "tickets" de tous les etickets liés à l'utilisateur
    tickets = request.user.eticket_set.all()
    # Renvoi via "context" dans une vue définie dans tickets.html
    return render(request, 'eticketing/tickets.html', context={"tickets": tickets})


class SalesByOfferView(ListView):
    # Configuration de base de la vue
    model = Event # Spécifie le modèle de données à utiliser
    template_name = 'eticketing/vue_vente.html'
    context_object_name = 'event_list' # Nom de la variable contexte à utiliser dans le template

    def get_queryset(self):
        # Méthode qui récupère les données à afficher par la vue
        return Event.objects.annotate(
            total_sales=Count('eticket') # Ajoute un champ calculé qui compte le nb de billets associés à chq événement
        ).order_by('-total_sales') # Ordonne les événements par nb total de billets vendus, du plus grand au plus petit

    def get_context_data(self, **kwargs):
        # Cette méthode permet d'ajouter des données supplémentaires au contexte du template
        context = super().get_context_data(**kwargs) # Appel à la méthode parente pour obtenir le contexte de base
        event_sales_data = [] # Création d'une liste pour stocker les données de vente par offre pour chaque événement
        for event in context['event_list']:
            offers = Eticket.objects.filter(event=event).values('offer').annotate(total=Count('id')).order_by('offer')
            # Récupération et regroupement des billets par 'offer', comptage et tri par offre pour chaque événement
            event_sales_data.append({
                'event': event,
                'offers': offers
            })
        context['event_sales_data'] = event_sales_data # Ajout de la liste complète des données de vente au contexte
        return context


def generate_sales_pdf(request):
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # Définir les styles
    styles = getSampleStyleSheet()
    title_style = styles['Title']
    normal_style = styles['Normal']

    # En-tête
    p.setFont("Helvetica-Bold", 16)
    p.drawString(100, height - 50, "Rapport de Ventes par Offre")

    # Pied de page
    p.setFont("Helvetica", 10)
    p.drawString(30, 30, "Rapport généré par notre système")

    # Calcul des ventes
    offer_counts = Eticket.objects.values('offer').annotate(total=Count('id'))
    total_sales = 0
    total_revenue = 0
    offer_sales = {'Solo': 0, 'Duo': 0, 'Familiale': 0}

    for offer in offer_counts:
        if offer['offer'] == 1:
            offer_sales['Solo'] = offer['total']
            total_revenue += offer['total'] * 50
        elif offer['offer'] == 2:
            offer_sales['Duo'] = offer['total']
            total_revenue += offer['total'] * 80
        elif offer['offer'] == 4:  # Mise à jour pour la valeur correcte de l'offre Familiale
            offer_sales['Familiale'] = offer['total']
            total_revenue += offer['total'] * 150
        total_sales += offer['total']

    # Création du graphique
    fig, ax = plt.subplots()
    labels = offer_sales.keys()
    sizes = offer_sales.values()
    ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
    ax.axis('equal')

    # Sauvegarde du graphique dans un objet BytesIO
    image_buffer = BytesIO()
    plt.savefig(image_buffer, format='png')
    plt.close(fig)
    image_buffer.seek(0)
    image = ImageReader(image_buffer)

    # Ajout du graphique au PDF
    p.drawImage(image, 50, height - 300, width=500, height=250)

    # Styliser les textes
    p.setFont("Helvetica-Bold", 12)
    p.drawString(100, height - 320, f"Nombre total de ventes: {total_sales}")
    p.drawString(100, height - 340, f"Revenu total: {total_revenue}€")

    # Ajout des données de ventes dans un tableau
    data = [['Offre', 'Nombre de Ventes', 'Revenu Total']]
    for offer, count in offer_sales.items():
        if offer == 'Solo':
            revenue = count * 50
        elif offer == 'Duo':
            revenue = count * 80
        elif offer == 'Familiale':
            revenue = count * 150
        data.append([offer, count, revenue])

    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))

    table.wrapOn(p, width, height)
    table.drawOn(p, 50, height - 500)

    # Finaliser et sauvegarder le PDF
    p.showPage()
    p.save()

    buffer.seek(0)
    return HttpResponse(buffer, content_type='application/pdf')










