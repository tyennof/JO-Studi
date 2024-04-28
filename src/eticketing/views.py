from django.db.models import Count
from django.shortcuts import render
from django.views.generic import ListView

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











