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

## Datos de prueba
```powershell
python manage.py cargar_datos
```
Usuarios (clave `Uncp2026*`): `admin1` (admin), `doc1`, `doc2`, `doc3` (docentes), `asist1` (asistente).

## Rutas
| Ruta | Acceso |
|---|---|
| `/catalogo/` | público (invitado) |
| `/login/`, `/logout/` | público |
| `/prestamos/` | admin, asistente (todos) / docente (propios) |
| `/prestamos/nuevo/` | docente, asistente |
| `/prestamos/<id>/devolver/` | solo asistente |
| `/equipos/<id>/eliminar/` | solo admin (POST) |
| `/auditoria/` | solo admin |
| `/admin/` | staff (Django Admin personalizado) |

## Seguridad
CSRF en todos los formularios POST, contraseñas con PBKDF2, cookies de sesión HttpOnly,
timeout de 30 min por inactividad, `select_related()` en listados (sin N+1).

## Avance
- [x] Esqueleto, sesiones y cookies seguras
- [x] Modelos y roles
- [x] Formularios con validaciones y sanitización (RF2)
- [x] Django Admin personalizado (RF1, RF5)
- [x] Middleware de auditoría y de préstamos vencidos (RF4)
- [x] Login/logout y vistas protegidas por rol (RF3)
- [x] Datos de prueba
- [ ] Capturas de evidencia (informe PDF)
