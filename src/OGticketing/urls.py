from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path

from accounts.views import signup, logout_user, login_user, UpdateProfile, set_default_shipping_address, delete_address, \
    contact, activate, UserChangePasswordView, UserChangePasswordDoneView, UserPasswordResetView, \
    UserPasswordResetDoneView, UserPasswordResetConfirmView, UserPasswordCompleteView
from event_mgmt.views import index_event_mgmt, event_detail, add_to_cart, cart, delete_cart, \
    create_checkout_session, checkout_success, stripe_webhook, update_quantities, accueil_site, mention, cgv
from eticketing.views import tickets, SalesByOfferView

from OGticketing import settings

urlpatterns = [

    path('', accueil_site, name='accueil-site'),
    path('admin/', admin.site.urls),
    path('mention', mention, name='mention'),
    path('cgv', cgv, name='cgv'),

    path('signup/', signup, name='signup'),
    path('activate/<uidb64>/<token>', activate, name='activate'),
    path('logout/', logout_user, name='logout'),
    path('login/', login_user, name='login'),
    path('change-password/', UserChangePasswordView.as_view(), name="change-password"),
    path('change-done/', UserChangePasswordDoneView.as_view(), name="change-done"),
    path('reset-password/', UserPasswordResetView.as_view(), name="reset"),
    path('reset-password-done/', UserPasswordResetDoneView.as_view(), name="reset-done"),
    path('reset-password-confirm/<str:uidb64>/<str:token>/', UserPasswordResetConfirmView.as_view(),
         name="reset-confirm"),
    path('reset-password-complete/', UserPasswordCompleteView.as_view(), name="reset-complete"),

    path('profile/<int:pk>', UpdateProfile.as_view(), name='profile'),
    path('profile/set_default_shipping/<int:pk>/', set_default_shipping_address, name='set-default-shipping'),
    path('delete_address/<int:pk>/', delete_address, name='delete-address'),
    path('contact/', contact, name='contact'),
    path('index_event_mgmt', index_event_mgmt, name='index-event-mgmt'),
    path('stripe_webhook/', stripe_webhook, name='stripe-webhook'),
    path('cart/', cart, name='cart'),
    path('cart/update_quantities/', update_quantities, name='update-quantities'),
    path('cart/success', checkout_success, name='checkout-success'),
    path('cart/delete/', delete_cart, name='delete-cart'),
    path('event_detail/<str:slug>', event_detail, name='event-detail'),
    path('event_detail/<str:slug>/add-to-cart/', add_to_cart, name='add-to-cart'),
    path('cart/create_checkout_session', create_checkout_session, name='create-checkout-session'),

    path('tickets', tickets, name='tickets'),
    path('ventes_par_offre/', SalesByOfferView.as_view(), name='ventes-par-offre'),


] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
