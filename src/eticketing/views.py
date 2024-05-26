import matplotlib
from django.shortcuts import render
from django.views.generic import ListView
import io

from django.db.models import Count
from django.http import HttpResponse
from django.contrib.admin.views.decorators import staff_member_required
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from matplotlib import pyplot as plt
matplotlib.use('Agg')  # Utilise le backend non interactif 'Agg'


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


@staff_member_required
def admin_report_view(request):
    return render(request, 'eticketing/admin_report.html')


@staff_member_required  # Décorateur pour restreindre l'accès aux administrateurs
def generate_sales_report(request):
    # Extraire les données de ventes de billets
    sales_data = Eticket.objects.values('offer').annotate(total_sales=Count('offer')).order_by('offer')

    # Initialiser les offres et les ventes correspondantes
    offers = ["Solo", "Duo", "Familiale"]
    sales = [0, 0, 0]

    # Remplir les données de ventes pour chaque offre
    for data in sales_data:
        sales[data['offer']] = data['total_sales']

    # Générer un graphique avec Matplotlib
    plt.figure(figsize=(10, 6))
    plt.bar(offers, sales, color=['blue', 'green', 'red'])
    plt.xlabel('Offers')
    plt.ylabel('Number of Sales')
    plt.title('Sales by Offer')
    plt.tight_layout()

    # Sauvegarder le graphique dans un objet BytesIO
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    plt.close()

    # Créer un objet PDF en utilisant le buffer comme "fichier"
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="sales_report.pdf"'
    p = canvas.Canvas(response, pagesize=letter)

    # Dessiner l'image du graphique dans le PDF
    p.drawImage(ImageReader(buffer), 50, 500, width=500, height=300)

    # Ajouter des données de résumé dans le PDF
    total_sales = sum(sales)
    p.drawString(100, 450, f"Total sales for 'Solo': {sales[0]}")
    p.drawString(100, 430, f"Total sales for 'Duo': {sales[1]}")
    p.drawString(100, 410, f"Total sales for 'Familiale': {sales[2]}")
    p.drawString(100, 390, f"Total sales: {total_sales}")

    # Terminer le document PDF proprement
    p.showPage()
    p.save()
    buffer.close()

    # Retourner le PDF en tant que réponse HTTP
    return response









