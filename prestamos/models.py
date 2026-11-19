"""Modelos del Sistema de Gestión de Préstamos de Equipos de Laboratorio."""
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models
from django.utils import timezone


class Laboratorio(models.Model):
    nombre = models.CharField(max_length=80, unique=True)
    ubicacion = models.CharField("ubicación", max_length=120, blank=True)

    class Meta:
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class Equipo(models.Model):
    class Categoria(models.TextChoices):
        LAPTOP = "laptop", "Laptop"
        PROYECTOR = "proyector", "Proyector"
        CAMARA = "camara", "Cámara"
        ARDUINO = "arduino", "Kit Arduino"
        ROUTER = "router", "Router"
        SWITCH = "switch", "Switch"

    class Estado(models.TextChoices):
        OPERATIVO = "operativo", "Operativo"
        MANTENIMIENTO = "mantenimiento", "En mantenimiento"
        BAJA = "baja", "Dado de baja"

    codigo_patrimonial = models.CharField(
        max_length=20,
        unique=True,
        validators=[
            RegexValidator(
                r"^[A-Z0-9-]{4,20}$",
                "Use de 4 a 20 caracteres: mayúsculas, números o guiones.",
            )
        ],
    )
    nombre = models.CharField(max_length=100)
    marca = models.CharField(max_length=60)
    modelo = models.CharField(max_length=60)
    categoria = models.CharField(max_length=20, choices=Categoria.choices)
    estado = models.CharField(
        max_length=20, choices=Estado.choices, default=Estado.OPERATIVO
    )
    laboratorio = models.ForeignKey(
        Laboratorio, on_delete=models.PROTECT, related_name="equipos"
    )
    stock_total = models.PositiveIntegerField(
        default=1, validators=[MinValueValidator(1)]
    )
    stock_disponible = models.PositiveIntegerField(default=1)
    fecha_ultimo_mantenimiento = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["codigo_patrimonial"]

    def __str__(self):
        return f"{self.codigo_patrimonial} - {self.nombre}"

    def clean(self):
        if self.stock_disponible > self.stock_total:
            raise ValidationError(
                {"stock_disponible": "El stock disponible no puede superar al stock total."}
            )

    # --- Campos calculados (RF1) ---
    @property
    def dias_desde_mantenimiento(self):
        if not self.fecha_ultimo_mantenimiento:
            return None
        return (timezone.localdate() - self.fecha_ultimo_mantenimiento).days

    @property
    def color_estado(self):
        return {
            self.Estado.OPERATIVO: "green",
            self.Estado.MANTENIMIENTO: "orange",
            self.Estado.BAJA: "red",
        }.get(self.estado, "gray")


class Prestamo(models.Model):
    class Estado(models.TextChoices):
        ACTIVO = "activo", "Activo"
        DEVUELTO = "devuelto", "Devuelto"
        VENCIDO = "vencido", "Vencido"

    class EstadoRetorno(models.TextChoices):
        BUENO = "bueno", "Buen estado"
        DANADO = "danado", "Dañado"
        MANTENIMIENTO = "mantenimiento", "Requiere mantenimiento"

    docente = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="prestamos"
    )
    equipo = models.ForeignKey(
        Equipo, on_delete=models.PROTECT, related_name="prestamos"
    )
    cantidad = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    fecha_prestamo = models.DateField(default=timezone.localdate)
    fecha_devolucion_prevista = models.DateField()
    fecha_devolucion_real = models.DateTimeField(null=True, blank=True)
    estado = models.CharField(
        max_length=10, choices=Estado.choices, default=Estado.ACTIVO
    )
    estado_equipo_devolucion = models.CharField(
        max_length=15, choices=EstadoRetorno.choices, blank=True
    )
    observaciones = models.TextField(blank=True)
    registrado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="prestamos_registrados",
    )
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-fecha_prestamo", "-id"]

    def __str__(self):
        return f"{self.equipo.codigo_patrimonial} -> {self.docente} ({self.estado})"

    def clean(self):
        if (
            self.fecha_prestamo
            and self.fecha_devolucion_prevista
            and self.fecha_devolucion_prevista <= self.fecha_prestamo
        ):
            raise ValidationError(
                {"fecha_devolucion_prevista": "La fecha de devolución debe ser posterior a la fecha de préstamo."}
            )

    # --- Campo calculado (RF5) ---
    @property
    def dias_retraso(self):
        if self.fecha_devolucion_real:
            referencia = timezone.localtime(self.fecha_devolucion_real).date()
        else:
            referencia = timezone.localdate()
        return max((referencia - self.fecha_devolucion_prevista).days, 0)


class RegistroAuditoria(models.Model):
    """Bitácora de acciones críticas (RF4). Solo visible para administradores."""

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    accion = models.CharField(max_length=60)
    detalle = models.TextField(blank=True)
    ruta = models.CharField(max_length=200, blank=True)
    ip = models.GenericIPAddressField(null=True, blank=True)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-fecha"]
        verbose_name = "registro de auditoría"
        verbose_name_plural = "registros de auditoría"

    def __str__(self):
        return f"{self.fecha:%Y-%m-%d %H:%M} {self.accion} ({self.usuario})"
