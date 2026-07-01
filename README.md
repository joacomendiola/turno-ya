# TurnoYa 🏥

Sistema web de gestión de turnos médicos desarrollado con Django 5.1+.  
Permite registrar médicos, pacientes y turnos, con autenticación de usuarios y panel de administración.

---

## 🛠️ Stack

| Tecnología | Versión |
|------------|---------|
| Python | 3.13+ |
| Django | 5.1+ |
| Base de datos | SQLite (desarrollo) |
| Frontend | Bootstrap 5 |
| Tests | `django.test.TestCase` |
| Control de versiones | Git + GitHub |

---

## ✨ Funcionalidades

- 🔐 Registro, login y logout de usuarios
- 👨‍⚕️ Gestión de médicos y especialidades
- 🧑 Gestión de pacientes
- 📅 Solicitud, confirmación y cancelación de turnos
- 📊 Panel de inicio con estadísticas del día
- 🛠️ Panel de administración Django configurado
- 📱 Interfaz responsiva con Bootstrap 5

---

## 👥 Integrantes

| Nombre | Usuario GitHub |
|--------|---------------|
| Joaquin Mendiola | [@joacomendiola](https://github.com/joacomendiola) |
| Gaston Mendiola | [@GAMS01](https://github.com/GAMS01) |
| Alexis Chambi | [@Alewch](https://github.com/Alewch) |
| Nehuen hervias | [@nehuen-hervias](https://github.com/nehuen-hervias) |

---

## 🚀 Instalación y uso

### 1. Clonar el repositorio

```bash
git clone https://github.com/usuario/turnoya.git
cd turnoya
```

### 2. Crear y activar el entorno virtual

```bash
# Windows
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Aplicar migraciones

```bash
python manage.py migrate
```

### 5. Crear superusuario (para el panel admin)

```bash
python manage.py createsuperuser
```

### 6. Correr el servidor de desarrollo

```bash
python manage.py runserver
```

Accedé a [http://localhost:8000](http://localhost:8000)  
Panel admin: [http://localhost:8000/admin](http://localhost:8000/admin)

---

## 🧪 Correr los tests

```bash
# Todos los tests con detalle
python manage.py test -v 2

# Solo tests de modelos
python manage.py test app.tests.test_models -v 2

# Solo tests de vistas
python manage.py test app.tests.test_views -v 2
```

---

## 🔑 Credenciales de prueba

> ⚠️ Solo para uso en el entorno de desarrollo local. Todos los usuarios de prueba comparten la misma contraseña.

| Rol | Usuario | Contraseña |
|-----|---------|-----------|
| **Administrador (Staff)** | `usuarioadmin` | `admin12345` |
| **Médico de prueba** | `medico` | `admin12345` |
| **Paciente de prueba** | `paciente` | `admin12345` |

---

## 📁 Estructura del proyecto

```
turno-ya/
├── turnoya/                # Configuración del proyecto Django (settings, urls, asgi, wsgi)
│   ├── settings.py
│   └── urls.py
├── app/                    # Aplicación principal del sistema
│   ├── models/             # Modelos de la base de datos (Estructura modular)
│   │   ├── init.py
│   │   ├── ausencia.py
│   │   ├── especialidad.py
│   │   ├── medico.py
│   │   ├── obraSocial.py
│   │   ├── paciente.py
│   │   ├── recordatorio.py
│   │   └── turno.py
│   ├── templates/          # Plantillas HTML estructuradas
│   │   ├── base.html
│   │   ├── clinica/        # Vistas de turnos, historiales, perfiles y ausencias
│   │   └── auth/           # Vistas de login y registro
│   ├── migrations/         # Historial de migraciones de la base de datos
│   ├── tests/              # Pruebas automatizadas (Models y Views)
│   │   ├── test_models.py
│   │   └── test_views.py
│   ├── admin.py            # Configuración del panel de administración de Django
│   ├── apps.py
│   ├── forms.py            # Formularios de la aplicación
│   ├── urls.py             # Enrutamiento interno de la app
│   └── views.py            # Lógica de las vistas y controladores del negocio
├── db.sqlite3              # Base de datos local (Desarrollo)
├── manage.py               # Script de gestión de Django
├── requirements.txt        # Dependencias del proyecto
└── .gitignore              # Archivos excluidos del control de versiones
```

---

## 🖼️ Capturas

### Inicio
![Pantalla de inicio](docs/screenshots/inicio.png)

### Lista de turnos
![Lista de turnos](docs/screenshots/turnos.png)

### Panel de administración
![Admin](docs/screenshots/admin.png)

### Login
![Login](docs/screenshots/login.png)

---

## 🧩 Decisiones de diseño

El proyecto fue pensado como una solución simple pero completa para administrar turnos médicos en un entorno de práctica académica. Elegimos este dominio porque permite modelar relaciones reales entre pacientes, médicos, especialidades, ausencias y turnos, y porque obliga a resolver validaciones de negocio que son fáciles de justificar y de probar. Esa combinación lo hace útil para demostrar tanto el uso de Django como el diseño de reglas de negocio.

La separación de responsabilidades se hizo intentando mantener el código legible. Los modelos concentran la lógica de negocio principal: validaciones de datos, creación y actualización de instancias, y reglas como evitar solapamientos de ausencias o turnos duplicados. Las vistas se encargan del flujo web y de la navegación, usando CBV cuando el comportamiento es estándar y simplifica el código. Los formularios quedan para validaciones de interfaz y de experiencia de usuario, como impedir fechas pasadas al pedir un turno.

La decisión de validar en el modelo y no únicamente en el formulario responde a que la integridad de los datos no debe depender de una sola pantalla. Si una regla es importante para el negocio, conviene que también viva en el modelo, así se protege tanto el acceso desde la web como cualquier otro punto de creación de datos. Por eso, por ejemplo, la validación de ausencias y la disponibilidad del médico están en el modelo de turno.

En cuanto a la organización del trabajo, se dividieron las responsabilidades por módulos: infraestructura y autenticación, médicos y disponibilidad, pacientes y turnos, e interfaz y administración. Eso permitió avanzar en paralelo sin pisarse demasiado. También se mantuvo un criterio común en los nombres de commits y en la estructura de templates para que el repositorio quedara más fácil de revisar.

Otra decisión importante fue usar `User` de Django como base de autenticación y vincularlo con `Paciente` mediante una relación uno a uno. Esa solución evita duplicar la lógica de login y aprovecha lo que ya trae Django, mientras que `Paciente` se usa para los datos propios del dominio clínico. Finalmente, se eligió Bootstrap 5 para lograr una interfaz funcional y responsiva sin agregar complejidad extra al frontend.

---

## ⭐ Funcionalidades opcionales implementadas

- [ ] Vista "Mis turnos" para el paciente autenticado
- [ ] Mensajes flash con `django.contrib.messages`
- [ ] Paginación en lista de turnos
- [ ] Permisos diferenciados por grupo
- [ ] Tests de integración (flujo completo)

---

## 🐛 Problemas comunes

| Problema | Solución |
|----------|----------|
| `OperationalError: no such table` | Corré `python manage.py migrate` |
| `No module named django` | Activá el entorno virtual |
| Página en blanco o error 500 | Revisá la consola donde corre `runserver` |
| Login no redirige bien | Verificá `LOGIN_REDIRECT_URL` en `settings.py` |
