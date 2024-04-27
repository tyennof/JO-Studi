from django.shortcuts import render


def tickets(request):
    # Récupération dans une variable "tickets" de tous les etickets liés à l'utilisateur
    tickets = request.user.eticket_set.all()
    # Renvoi via "context" dans une vue définie dans tickets.html
    return render(request, 'eticketing/tickets.html', context={"tickets": tickets})













