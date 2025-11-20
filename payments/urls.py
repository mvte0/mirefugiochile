from django.urls import path

from . import views

app_name = "payments"

urlpatterns = [
    path("", views.donation_form, name="crear"),
    path("historial/", views.donation_history, name="historial"),
    path("retorno/", views.webpay_return, name="webpay_return"),
    path("estado/", views.webpay_status, name="webpay_status"),
]
