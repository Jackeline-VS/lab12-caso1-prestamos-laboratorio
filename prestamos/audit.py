"""Utilidades de auditoría (RF4): IP del cliente y registro de acciones críticas."""
import logging

from .models import RegistroAuditoria

logger = logging.getLogger("auditoria")


def obtener_ip(request):
    # Se usa REMOTE_ADDR: X-Forwarded-For puede ser falsificado por el cliente.
    return request.META.get("REMOTE_ADDR")


def auditar(request, accion, detalle=""):
    """Guarda en BD y en el log: usuario, fecha/hora, IP y acción realizada."""
    usuario = request.user if request.user.is_authenticated else None
    ip = obtener_ip(request)
    RegistroAuditoria.objects.create(
        usuario=usuario, accion=accion, detalle=detalle, ruta=request.path, ip=ip
    )
    logger.info(
        "ACCION=%s usuario=%s ip=%s detalle=%s",
        accion, usuario.username if usuario else "anonimo", ip, detalle,
    )
