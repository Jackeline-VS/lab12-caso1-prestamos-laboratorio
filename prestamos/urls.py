from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    path("", views.inicio, name="inicio"),
    path("catalogo/", views.catalogo, name="catalogo"),
    path("login/", auth_views.LoginView.as_view(), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("prestamos/", views.mis_prestamos, name="prestamos"),
    path("prestamos/nuevo/", views.solicitar_prestamo, name="solicitar_prestamo"),
    path("prestamos/<int:pk>/devolver/", views.registrar_devolucion, name="devolver"),
    path("equipos/<int:pk>/eliminar/", views.eliminar_equipo, name="eliminar_equipo"),
    path("auditoria/", views.auditoria, name="auditoria"),
]
