"""Carga datos de prueba: 5 laboratorios, 12 equipos, 5 usuarios y 15 préstamos."""
from datetime import datetime, time, timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from prestamos.models import Equipo, Laboratorio, Prestamo
from prestamos.roles import ROL_ADMIN, ROL_ASISTENTE, ROL_DOCENTE, ROLES

CLAVE = "Uncp2026*"

USUARIOS = [
    ("admin1", "Ana", "Quispe", ROL_ADMIN),
    ("doc1", "Luis", "Mendoza", ROL_DOCENTE),
    ("doc2", "María", "Rojas", ROL_DOCENTE),
    ("doc3", "Carlos", "Huamán", ROL_DOCENTE),
    ("asist1", "Rosa", "Paucar", ROL_ASISTENTE),
]

# codigo, nombre, marca, modelo, categoria, lab(1-5), stock_total, estado, dias_mant
EQUIPOS = [
    ("LAP-0001", "Laptop Dell", "Dell", "Latitude 5420", "laptop", 1, 5, "operativo", 40),
    ("LAP-0002", "Laptop HP", "HP", "ProBook 440", "laptop", 2, 5, "operativo", 95),
    ("LAP-0003", "Laptop Lenovo", "Lenovo", "ThinkPad E14", "laptop", 3, 5, "operativo", 10),
    ("PRY-0001", "Proyector Epson", "Epson", "X49", "proyector", 1, 3, "operativo", 60),
    ("PRY-0002", "Proyector BenQ", "BenQ", "MS550", "proyector", 3, 2, "mantenimiento", 5),
    ("CAM-0001", "Cámara web", "Logitech", "C920", "camara", 2, 4, "operativo", 120),
    ("ARD-0001", "Kit Arduino UNO", "Arduino", "UNO R3", "arduino", 4, 10, "operativo", 30),
    ("ARD-0002", "Kit Arduino Mega", "Arduino", "Mega 2560", "arduino", 4, 6, "operativo", 30),
    ("RTR-0001", "Router Cisco", "Cisco", "ISR1100", "router", 5, 3, "operativo", 200),
    ("RTR-0002", "Router TP-Link", "TP-Link", "Archer C6", "router", 5, 4, "baja", 400),
    ("SWT-0001", "Switch Cisco", "Cisco", "Catalyst 2960", "switch", 5, 4, "operativo", 150),
    ("SWT-0002", "Switch D-Link", "D-Link", "DGS-1100", "switch", 3, 3, "operativo", 75),
]

# docente, equipo, cantidad, hace_dias, plazo_dias, devuelto?
PRESTAMOS = [
    ("doc1", "LAP-0001", 1, 40, 7, True),
    ("doc2", "PRY-0001", 1, 35, 5, True),
    ("doc3", "CAM-0001", 1, 30, 7, True),
    ("doc1", "ARD-0001", 2, 25, 10, True),
    ("doc2", "SWT-0001", 1, 20, 7, True),
    ("doc3", "RTR-0001", 1, 12, 7, True),
    ("doc1", "LAP-0002", 1, 20, 7, False),   # vencido
    ("doc1", "PRY-0001", 1, 2, 7, False),
    ("doc1", "ARD-0002", 2, 3, 14, False),
    ("doc2", "LAP-0003", 1, 15, 7, False),   # vencido
    ("doc2", "CAM-0001", 1, 1, 7, False),
    ("doc2", "SWT-0002", 1, 4, 10, False),
    ("doc3", "LAP-0001", 1, 18, 10, False),  # vencido
    ("doc3", "RTR-0001", 1, 2, 7, False),
    ("doc3", "ARD-0001", 3, 5, 14, False),
]


class Command(BaseCommand):
    help = "Carga datos de prueba (idempotente)."

    @transaction.atomic
    def handle(self, *args, **options):
        User = get_user_model()
        grupos = {r: Group.objects.get_or_create(name=r)[0] for r in ROLES}
        usuarios = {}
        for username, nombre, apellido, rol in USUARIOS:
            u, creado = User.objects.get_or_create(
                username=username,
                defaults=dict(
                    first_name=nombre, last_name=apellido,
                    email=f"{username}@uncp.edu.pe",
                    is_staff=(rol == ROL_ADMIN), is_superuser=(rol == ROL_ADMIN),
                ),
            )
            if creado:
                u.set_password(CLAVE)
                u.save()
            u.groups.add(grupos[rol])
            usuarios[username] = u

        labs = {
            i: Laboratorio.objects.get_or_create(
                nombre=f"Laboratorio {i}", defaults={"ubicacion": f"Pabellón A, piso {i}"}
            )[0]
            for i in range(1, 6)
        }
        hoy = timezone.localdate()
        equipos = {}
        for cod, nom, marca, modelo, cat, lab, total, estado, dias in EQUIPOS:
            equipos[cod], _ = Equipo.objects.get_or_create(
                codigo_patrimonial=cod,
                defaults=dict(
                    nombre=nom, marca=marca, modelo=modelo, categoria=cat,
                    laboratorio=labs[lab], stock_total=total, stock_disponible=total,
                    estado=estado, fecha_ultimo_mantenimiento=hoy - timedelta(days=dias),
                ),
            )

        if Prestamo.objects.exists():
            self.stdout.write("Los préstamos ya existen: no se duplican.")
            return

        for doc, cod, cant, hace, plazo, devuelto in PRESTAMOS:
            inicio = hoy - timedelta(days=hace)
            prevista = inicio + timedelta(days=plazo)
            real = None
            if devuelto:
                estado = Prestamo.Estado.DEVUELTO
                real = timezone.make_aware(datetime.combine(inicio + timedelta(days=plazo - 1), time(10, 0)))
            else:
                estado = Prestamo.Estado.ACTIVO if prevista >= hoy else Prestamo.Estado.VENCIDO
                eq = equipos[cod]
                eq.stock_disponible -= cant
                eq.save(update_fields=["stock_disponible"])
            Prestamo.objects.create(
                docente=usuarios[doc], equipo=equipos[cod], cantidad=cant,
                fecha_prestamo=inicio, fecha_devolucion_prevista=prevista,
                fecha_devolucion_real=real, estado=estado,
                estado_equipo_devolucion="bueno" if devuelto else "",
                registrado_por=usuarios["asist1"],
            )
        self.stdout.write(self.style.SUCCESS(
            f"Datos cargados. Usuarios: admin1, doc1-3, asist1 | clave: {CLAVE}"
        ))
