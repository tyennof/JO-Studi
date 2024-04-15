from django import forms
from event_mgmt.models import Order


# Création formulaire pour ne modifier que la quantité dans le panier

OFFRES = (
    (1, "Offre Solo -> 1 place"),
    (2, "Offre Duo  -> 2 places"),
    (4, "Offre Familiale -> 4 places")
)


class OrderForm(forms.ModelForm):
    # Changer l'offre
    quantity = forms.ChoiceField(choices=OFFRES)
    # Supprimer l'article
    delete = forms.BooleanField(initial=False, required=False, label="Supprimer cette réservation")

    class Meta:
        model = Order
        fields = ["quantity"]

    def save(self, *args, **kwargs):
        if self.cleaned_data["delete"]:
            return self.instance.delete()

        return super().save(*args, **kwargs)

