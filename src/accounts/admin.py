from django.contrib import admin

from accounts.models import CustomUser, ShippingAddress

admin.site.register(CustomUser)
admin.site.register(ShippingAddress)

