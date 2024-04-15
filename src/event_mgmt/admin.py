from django.contrib import admin
from event_mgmt.models import Event, Order, Cart

# Register your models here.
admin.site.register(Event)
admin.site.register(Order)
admin.site.register(Cart)
