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
