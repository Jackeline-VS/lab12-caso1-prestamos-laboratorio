"""Django Admin personalizado (RF1 y RF5)."""
import logging

from django.contrib import admin, messages
from django.utils.html import format_html

from .models import Equipo, Laboratorio, Prestamo, RegistroAuditoria

logger = logging.getLogger("auditoria")


@admin.register(Laboratorio)
class LaboratorioAdmin(admin.ModelAdmin):
    list_display = ("nombre", "ubicacion")
    search_fields = ("nombre",)


@admin.register(Equipo)
class EquipoAdmin(admin.ModelAdmin):
    list_display = (
        "codigo_patrimonial", "nombre", "categoria", "laboratorio",
        "estado_visual", "stock_disponible", "stock_total", "dias_mantenimiento",
    )
    list_filter = ("laboratorio", "estado")
    search_fields = ("codigo_patrimonial", "nombre", "categoria")
    list_select_related = ("laboratorio",)
    actions = ["marcar_en_mantenimiento"]

    @admin.display(description="Estado")
    def estado_visual(self, obj):
        return format_html(
            '<b style="color:{}">{}</b>', obj.color_estado, obj.get_estado_display()
        )

    @admin.display(description="Días desde último mantenimiento")
    def dias_mantenimiento(self, obj):
        dias = obj.dias_desde_mantenimiento
        return "Sin registro" if dias is None else dias

    @admin.action(description="Marcar como en mantenimiento")
    def marcar_en_mantenimiento(self, request, queryset):
        n = queryset.update(estado=Equipo.Estado.MANTENIMIENTO)
        logger.info("ADMIN ACCION=marcar_mantenimiento usuario=%s equipos=%s", request.user, n)
        self.message_user(request, f"{n} equipo(s) marcados como en mantenimiento.", messages.SUCCESS)


@admin.register(Prestamo)
class PrestamoAdmin(admin.ModelAdmin):
    list_display = (
        "docente", "equipo", "fecha_prestamo", "fecha_devolucion_prevista",
        "estado", "dias_de_retraso",
    )
    list_filter = ("fecha_prestamo", "estado", "docente")
    search_fields = (
        "equipo__codigo_patrimonial", "equipo__nombre",
        "docente__first_name", "docente__last_name", "docente__username",
    )
    list_select_related = ("docente", "equipo")  # evita consultas N+1
    date_hierarchy = "fecha_prestamo"
    actions = ["enviar_recordatorio_devolucion"]

    @admin.display(description="Días de retraso")
    def dias_de_retraso(self, obj):
        if obj.estado == Prestamo.Estado.DEVUELTO and not obj.dias_retraso:
            return 0
        return obj.dias_retraso

    @admin.action(description="Enviar recordatorio de devolución")
    def enviar_recordatorio_devolucion(self, request, queryset):
        pendientes = queryset.exclude(estado=Prestamo.Estado.DEVUELTO)
        for p in pendientes:
            logger.info(
                "RECORDATORIO devolucion docente=%s equipo=%s vence=%s",
                p.docente, p.equipo.codigo_patrimonial, p.fecha_devolucion_prevista,
            )
        self.message_user(
            request, f"Recordatorio enviado para {pendientes.count()} préstamo(s) pendiente(s).",
            messages.SUCCESS,
        )


@admin.register(RegistroAuditoria)
class RegistroAuditoriaAdmin(admin.ModelAdmin):
    """Bitácora de solo lectura, visible únicamente para superusuarios."""

    list_display = ("fecha", "usuario", "accion", "ip", "ruta")
    list_filter = ("accion", "fecha")
    search_fields = ("usuario__username", "accion", "detalle")
    readonly_fields = ("usuario", "accion", "detalle", "ruta", "ip", "fecha")

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_module_permission(self, request):
        return request.user.is_superuser

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
