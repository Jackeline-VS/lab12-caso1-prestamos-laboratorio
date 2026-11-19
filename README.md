# Caso 1 - Sistema de Gestión de Préstamos de Equipos de Laboratorio

**Práctica Grupal Semana 12** - Desarrollo de Aplicaciones Web (IS093A) - UNCP,
Facultad de Ingeniería de Sistemas.
Temas: formularios, Django Admin, middleware, sesiones, autenticación y autorización.

**Autora:** Jackeline Vivanco Solano (código 2022100549I)

## Requisitos
- Python 3.10 o superior
- Git

## Instalación (Windows, PowerShell)
```powershell
git clone https://github.com/Jackeline-VS/lab12-caso1-prestamos-laboratorio.git
cd lab12-caso1-prestamos-laboratorio
py -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python manage.py makemigrations prestamos
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```
Abrir http://127.0.0.1:8000/admin/

> `db.sqlite3` y `venv/` no se versionan (ver `.gitignore`). Los datos de prueba se
> cargan con el comando de carga inicial (pendiente de implementar, ver avance).

## Roles (grupos de Django)
| Rol | Permisos |
|---|---|
| admin | CRUD de equipos, usuarios y reportes; elimina equipos; ve la auditoría |
| docente | Solicita préstamos y ve solo su historial |
| asistente | Registra préstamos y devoluciones |
| invitado | Solo catálogo (lectura) |

## Estructura
```
config/        settings, urls, wsgi/asgi
prestamos/     app: models, roles, (forms, views, admin, middleware)
templates/     plantillas
```

## Flujo de trabajo Git
- `main`: rama estable, solo recibe Pull Requests.
- `dev/integrante-1`: modelos, formularios, validaciones, admin, plantillas.
- `dev/integrante-2`: settings, middleware, autenticación, autorización, sesiones.

## Avance
- [x] Esqueleto del proyecto y configuración de sesiones/cookies
- [x] Modelos: Laboratorio, Equipo, Prestamo, RegistroAuditoria
- [x] Roles y constantes de autorización
- [ ] Formularios con validaciones (RF2)
- [ ] Django Admin personalizado (RF1, RF5)
- [ ] Middleware de auditoría (RF4)
- [ ] Login/logout y vistas protegidas por rol (RF3)
- [ ] Datos de prueba (10 equipos, 5 usuarios, 15 préstamos)
