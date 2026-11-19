"""Formularios del Caso 1 (RF2): validaciones, validación cruzada y sanitización."""
import re
from datetime import timedelta

from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.html import strip_tags

from .models import Equipo, Prestamo
from .roles import MAX_PRESTAMOS_ACTIVOS, ROL_DOCENTE, es_asistente

MAX_DIAS_PRESTAMO = 90


def sanitizar_texto(valor):
    """Elimina etiquetas HTML y normaliza espacios (evita XSS almacenado)."""
    valor = strip_tags(valor or "")
    return re.sub(r"\s+", " ", valor).strip()


class PrestamoForm(forms.ModelForm):
    """Solicitud de préstamo. Si quien la llena es asistente, elige al docente."""

    class Meta:
        model = Prestamo
        fields = ["equipo", "cantidad", "fecha_devolucion_prevista", "observaciones"]
        widgets = {
            "fecha_devolucion_prevista": forms.DateInput(
                attrs={"type": "date"}, format="%Y-%m-%d"
            ),
            "observaciones": forms.Textarea(attrs={"rows": 3}),
        }
        labels = {"fecha_devolucion_prevista": "Fecha de devolución"}

    def __init__(self, *args, usuario, **kwargs):
        super().__init__(*args, **kwargs)
        self.usuario = usuario
        self.fields["equipo"].queryset = Equipo.objects.select_related("laboratorio")
        if es_asistente(usuario):
            self.fields["docente"] = forms.ModelChoiceField(
                queryset=get_user_model().objects.filter(groups__name=ROL_DOCENTE),
                label="Docente",
            )
            self.order_fields(
                ["docente", "equipo", "cantidad", "fecha_devolucion_prevista", "observaciones"]
            )

    # --- validaciones por campo ---
    def clean_equipo(self):
        equipo = self.cleaned_data["equipo"]
        if equipo.estado != Equipo.Estado.OPERATIVO:
            raise ValidationError(
                f"El equipo {equipo.codigo_patrimonial} está en estado "
                f"'{equipo.get_estado_display()}' y no puede prestarse."
            )
        return equipo

    def clean_fecha_devolucion_prevista(self):
        fecha = self.cleaned_data["fecha_devolucion_prevista"]
        limite = timezone.localdate() + timedelta(days=MAX_DIAS_PRESTAMO)
        if fecha > limite:
            raise ValidationError(
                f"El préstamo no puede exceder {MAX_DIAS_PRESTAMO} días."
            )
        return fecha

    def clean_observaciones(self):
        return sanitizar_texto(self.cleaned_data.get("observaciones"))

    # --- validación cruzada ---
    def clean(self):
        cleaned = super().clean()
        docente = cleaned.get("docente") or self.usuario
        equipo = cleaned.get("equipo")
        cantidad = cleaned.get("cantidad")

        activos = Prestamo.objects.filter(
            docente=docente,
            estado__in=[Prestamo.Estado.ACTIVO, Prestamo.Estado.VENCIDO],
        ).count()
        if activos >= MAX_PRESTAMOS_ACTIVOS:
            raise ValidationError(
                f"{docente.get_full_name() or docente.username} ya tiene {activos} "
                f"préstamos activos (máximo {MAX_PRESTAMOS_ACTIVOS})."
            )

        if equipo and cantidad and cantidad > equipo.stock_disponible:
            self.add_error(
                "cantidad",
                f"Solo hay {equipo.stock_disponible} unidad(es) disponible(s) de "
                f"{equipo.nombre}; solicitó {cantidad}.",
            )
        return cleaned
