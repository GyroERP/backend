"""URL configuration for GyroERP."""

from django.contrib import admin
from django.urls import include, path

from gyroerp.views import health_check

urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/", health_check, name="health-check"),
    path("api/kernel/", include("gyrokernel.urls")),
]
