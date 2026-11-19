"""Vistas protegidas por rol (RF3). CSRF activo en todos los formularios POST."""
from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import F, ProtectedError
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .audit import auditar
from .forms import DevolucionForm, PrestamoForm
from .models import Equipo, Prestamo, RegistroAuditoria
from .roles import es_admin, es_asistente, es_docente


def rol_requerido(*verificadores):
    """Exige login y que el usuario cumpla al menos uno de los roles indicados."""

    def decorador(vista):
        @wraps(vista)
        def envoltura(request, *args, **kwargs):
            if not any(v(request.user) for v in verificadores):
                raise PermissionDenied  # AuditoriaMiddleware lo registra (403)
            return vista(request, *args, **kwargs)

        return login_required(envoltura)

    return decorador


@login_required
def inicio(request):
    return render(request, "prestamos/inicio.html")


def catalogo(request):
    """Catálogo en modo lectura, visible para invitados."""
    equipos = Equipo.objects.select_related("laboratorio")
    return render(request, "prestamos/catalogo.html", {"equipos": equipos})


@rol_requerido(es_admin, es_asistente, es_docente)
def mis_prestamos(request):
    qs = Prestamo.objects.select_related("docente", "equipo", "equipo__laboratorio")
    if not (es_admin(request.user) or es_asistente(request.user)):
        qs = qs.filter(docente=request.user)  # los docentes solo ven los suyos
    return render(request, "prestamos/lista_prestamos.html", {"prestamos": qs})


@rol_requerido(es_docente, es_asistente)
def solicitar_prestamo(request):
    if request.method == "POST":
        form = PrestamoForm(request.POST, usuario=request.user)
        if form.is_valid():
            with transaction.atomic():
                equipo = Equipo.objects.select_for_update().get(
                    pk=form.cleaned_data["equipo"].pk
                )
                cantidad = form.cleaned_data["cantidad"]
                if cantidad > equipo.stock_disponible:
                    form.add_error("cantidad", "El stock cambió: ya no hay unidades suficientes.")
                else:
                    prestamo = form.save(commit=False)
                    prestamo.docente = form.cleaned_data.get("docente") or request.user
                    prestamo.registrado_por = request.user
                    prestamo.save()
                    equipo.stock_disponible -= cantidad
                    equipo.save(update_fields=["stock_disponible"])
                    auditar(
                        request, "PRESTAMO",
                        f"{equipo.codigo_patrimonial} x{cantidad} -> {prestamo.docente.username}",
                    )
                    messages.success(request, "Préstamo registrado correctamente.")
                    return redirect("prestamos")
    else:
        form = PrestamoForm(usuario=request.user)
    return render(request, "prestamos/formulario.html", {
        "form": form, "titulo": "Solicitud de préstamo", "boton": "Solicitar",
    })


@rol_requerido(es_asistente)
def registrar_devolucion(request, pk):
    prestamo = get_object_or_404(
        Prestamo.objects.select_related("equipo", "docente"),
        pk=pk, estado__in=[Prestamo.Estado.ACTIVO, Prestamo.Estado.VENCIDO],
    )
    form = DevolucionForm(request.POST or None, instance=prestamo)
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            p = form.save(commit=False)
            p.estado = Prestamo.Estado.DEVUELTO
            p.fecha_devolucion_real = timezone.now()
            p.registrado_por = request.user
            p.save()
            Equipo.objects.filter(pk=p.equipo_id).update(
                stock_disponible=F("stock_disponible") + p.cantidad
            )
            if p.estado_equipo_devolucion != Prestamo.EstadoRetorno.BUENO:
                Equipo.objects.filter(pk=p.equipo_id).update(
                    estado=Equipo.Estado.MANTENIMIENTO
                )
            auditar(
                request, "DEVOLUCION",
                f"{p.equipo.codigo_patrimonial} de {p.docente.username} ({p.estado_equipo_devolucion})",
            )
        messages.success(request, "Devolución registrada.")
        return redirect("prestamos")
    return render(request, "prestamos/formulario.html", {
        "form": form, "boton": "Registrar devolución",
        "titulo": f"Devolución de {prestamo.equipo}",
        "subtitulo": f"Docente: {prestamo.docente.get_full_name() or prestamo.docente.username}",
    })


@require_POST
@rol_requerido(es_admin)
def eliminar_equipo(request, pk):
    equipo = get_object_or_404(Equipo, pk=pk)
    codigo = equipo.codigo_patrimonial
    try:
        equipo.delete()
    except ProtectedError:
        messages.error(request, f"No se puede eliminar {codigo}: tiene préstamos asociados.")
    else:
        auditar(request, "ELIMINACION_EQUIPO", codigo)
        messages.success(request, f"Equipo {codigo} eliminado.")
    return redirect("catalogo")


@rol_requerido(es_admin)
def auditoria(request):
    registros = RegistroAuditoria.objects.select_related("usuario")[:200]
    return render(request, "prestamos/auditoria.html", {"registros": registros})
