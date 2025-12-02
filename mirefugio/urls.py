"""
URL configuration for mirefugio project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from core.views import api_sugerencias, landing
from core.views_auth import LoginViewRemember, logout_then_home

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", landing, name="home"),
    path("", include("core.urls")),       # raíz y API de contacto
    path("donar/", include(("payments.urls", "payments"), namespace="payments")),   # donaciones Webpay
    path("pagos/", include(("payments.urls", "payments"), namespace="payments_alias")), # Alias para compatibilidad con prod
    path("accounts/login/", LoginViewRemember.as_view(template_name="registration/login.html"), name="login"),
    path("accounts/logout/", logout_then_home, name="logout"),
    path("accounts/", include("django.contrib.auth.urls")),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

