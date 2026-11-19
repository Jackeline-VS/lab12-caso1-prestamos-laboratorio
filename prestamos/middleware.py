"""Middleware propios del Caso 1 (RF4)."""
import logging

from django.contrib import messages
from django.urls import reverse
from django.utils import timezone

from .audit import obtener_ip
from .models import Prestamo, RegistroAuditoria

logger = logging.getLogger("auditoria")


class AuditoriaMiddleware:
    """Registra cada petición y los intentos de acceso no autorizado."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if request.path.startswith(("/static/", "/favicon")):
            return response

        usuario = request.user if request.user.is_authenticated else None
        nombre = usuario.username if usuario else "anonimo"
        ip = obtener_ip(request)
        logger.info(
            "REQUEST %s %s -> %s | usuario=%s ip=%s",
            request.method, request.path, response.status_code, nombre, ip,
        )

        if response.status_code == 403:
            logger.warning(
                "ACCESO NO AUTORIZADO usuario=%s ip=%s ruta=%s", nombre, ip, request.path
            )
            RegistroAuditoria.objects.create(
                usuario=usuario, accion="ACCESO_NO_AUTORIZADO",
                detalle=f"{request.method} {request.path}", ruta=request.path, ip=ip,
            )
        elif (
            response.status_code == 302
            and usuario is None
            and response["Location"].startswith(reverse("login"))
        ):
            logger.warning(
                "INTENTO SIN AUTENTICAR ip=%s ruta=%s (redirigido a login)", ip, request.path
            )
        return response
