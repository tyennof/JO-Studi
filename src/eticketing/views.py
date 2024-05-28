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

    # Calculer la position pour centrer le titre
    title = "Rapport de ventes par offre pour la billetterie des J.O."
    title_x = (width - p.stringWidth(title, "Helvetica-Bold", 16)) / 2
    title_y = height - 50

    # En-tête
    p.setFont("Helvetica-Bold", 16)
    p.drawString(title_x, title_y, title)

    # Encadrer le titre
    p.setStrokeColor(colors.black)
    p.setLineWidth(1)
    p.rect(title_x - 10, title_y - 10, p.stringWidth(title, "Helvetica-Bold", 16) + 20, 30, stroke=1, fill=0)

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

    # Ajout du graphique au PDF avec une position ajustée
    p.drawImage(image, 50, height - 350, width=500, height=250)

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

    # Calculer la position pour centrer le tableau
    table_width, table_height = table.wrap(0, 0)
    table_x = (width - table_width) / 2
    table_y = height - 500  # Ajuster cette valeur si nécessaire pour éviter les chevauchements

    table.drawOn(p, table_x, table_y)

    # Styliser les textes pour le bas de la page
    p.setFont("Helvetica-Bold", 18)
    sales_text = f"Nombre total de ventes: {total_sales}"
    revenue_text = f"Revenu total: {total_revenue}€"
    sales_text_x = (width - p.stringWidth(sales_text, "Helvetica-Bold", 18)) / 2
    revenue_text_x = (width - p.stringWidth(revenue_text, "Helvetica-Bold", 18)) / 2
    p.drawString(sales_text_x, 200, sales_text)
    p.drawString(revenue_text_x, 160, revenue_text)

    # Finaliser et sauvegarder le PDF
    p.showPage()
    p.save()

    buffer.seek(0)
    return HttpResponse(buffer, content_type='application/pdf')













