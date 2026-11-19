"""Context processor: expone los roles del usuario a las plantillas."""
from .roles import es_admin, es_asistente, es_docente


def roles(request):
    u = request.user
    return {
        "rol_admin": es_admin(u),
        "rol_docente": es_docente(u),
        "rol_asistente": es_asistente(u),
    }
