"""Roles y reglas de autorización del Caso 1 (grupos de Django)."""

ROL_ADMIN = "admin"
ROL_DOCENTE = "docente"
ROL_ASISTENTE = "asistente"
ROLES = (ROL_ADMIN, ROL_DOCENTE, ROL_ASISTENTE)

MAX_PRESTAMOS_ACTIVOS = 3  # RF2: máximo de préstamos activos por docente


def tiene_rol(user, rol):
    return user.is_authenticated and user.groups.filter(name=rol).exists()


def es_admin(user):
    return user.is_authenticated and (user.is_superuser or tiene_rol(user, ROL_ADMIN))


def es_docente(user):
    return tiene_rol(user, ROL_DOCENTE)


def es_asistente(user):
    return tiene_rol(user, ROL_ASISTENTE)
