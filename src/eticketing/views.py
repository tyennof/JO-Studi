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
    model = Event
    template_name = 'eticketing/vue_vente.html'
    context_object_name = 'event_list'

    def get_queryset(self):
        return Event.objects.annotate(
            total_sales=Count('eticket')
        ).order_by('-total_sales')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        event_sales_data = []
        for event in context['event_list']:
            offers = Eticket.objects.filter(event=event).values('offer').annotate(total=Count('id')).order_by('offer')
            event_sales_data.append({
                'event': event,
                'offers': offers
            })
        context['event_sales_data'] = event_sales_data
        return context











