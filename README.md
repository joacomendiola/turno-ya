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

> ⚠️ Solo para uso del corrector en entorno de desarrollo local.

| Rol | Usuario | Contraseña |
|-----|---------|-----------|
| Superusuario / Admin | `admin` | `admin1234` |
| Usuario de prueba | `usuario_prueba` | `prueba1234` |

---

## 📁 Estructura del proyecto

```
turnoya/
├── turnoya/            # Configuración del proyecto Django
│   ├── settings.py
│   └── urls.py
├── app/                # App principal
│   ├── models.py       # Especialidad, Medico, Paciente, Turno
│   ├── views.py
│   ├── urls.py
│   ├── forms.py
│   ├── admin.py
│   ├── consultas.py    # Consultas ORM
│   └── tests/
│       ├── test_models.py
│       └── test_views.py
├── templates/
│   ├── base.html
│   └── registration/
├── static/
├── manage.py
├── requirements.txt
└── .gitignore
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

## 🗺️ Plan operativo de ejecución

### 1) Orden y dependencias (bloqueantes)
1. Modelos base + constraints: `User/Especialidad`, `ObraSocial/Médico`, `Paciente`, `Turno`, `Ausencia`.
2. Auth y permisos: login/logout/registro + roles funcionales.
3. Vistas backend: listado por rol, detalle médico, alta/cancelación/aceptación de turnos.
4. Consultas ORM avanzadas (`app/consultas.py`) para estadísticas y filtros.
5. UI/UX: home, navbar dinámica, formularios Bootstrap y tabla con filtro.
6. Opcionales: `FranjaHoraria`, reprogramación automática y recordatorios/historial (solo si lo obligatorio está cerrado).

### 2) Contratos obligatorios del equipo
- Estados de turno: `PENDIENTE`, `ACEPTADO`, `CANCELADO`.
- Roles y permisos funcionales: `PACIENTE`, `MEDICO`, `ADMIN`.
- Campos clave acordados: matrícula única (médico), DNI único (paciente), relación médico-especialidad, ausencias por rango fecha/hora.
- Rutas estándar: auth, médicos, pacientes, turnos y ausencias con naming consistente.
- Vistas con formato estable: mensajes de éxito/error + redirecciones esperadas.

### 3) Criterio de “Done” por tarea
- Modelo con validaciones + constraint real en DB.
- Vista protegida por permisos correctos.
- Caso feliz + caso inválido cubiertos.
- UI renderizada sin romper navegación.
- Commit con convención uniforme y mensaje claro.

### 4) Plan semanal de ejecución
#### Semana 1 (base técnica)
- Cerrar modelos obligatorios y migraciones.
- Cerrar auth/permisos.
- Definir y congelar contratos (estados, roles, rutas).

#### Semana 2 (flujo funcional)
- Implementar turnos completos: crear, listar por rol, aceptar, cancelar.
- Implementar detalle médico + ausencias.
- Integrar consultas ORM para home y filtros.

#### Semana 3 (UI + integración)
- Terminar home/navbar/formularios/tabla con filtro.
- Ejecutar pruebas de flujo manuales y automáticas mínimas.
- Ajustar hardening de permisos y detalles finales.

#### Semana 4 (buffer/opcionales)
- Implementar opcionales solo si lo obligatorio está estable.
- Cierre técnico y actualización final de documentación.

### 5) Plan de integración
- Integración diaria a rama común del equipo.
- Responsable rotativo diario para resolución de conflictos.
- Regla: no mergear sin pruebas mínimas verdes del módulo tocado.
- Freeze 24h antes de entrega: solo bugfix.

### 6) Testing mínimo por módulo
- Modelos: validaciones y constraints.
- Vistas: acceso permitido/denegado por rol.
- Flujos: crear turno, aceptar (médico), cancelar (paciente), ausencia.
- Consultas: estadísticas de home y filtro por especialidad.

### 7) Convención de commits
- `feat(modelos): ...`
- `feat(auth): ...`
- `feat(vistas): ...`
- `feat(ui): ...`
- `test(...): ...`
- `fix(...): ...`

### 8) Matriz mínima de seguridad/permisos
- Paciente: ver/editar perfil propio, crear/cancelar turnos propios, ver listado propio.
- Médico: ver sus turnos, aceptar/rechazar, gestionar ausencias propias.
- Admin: gestión global de catálogos, métricas y supervisión.
- Regla transversal: ningún usuario accede o edita recursos ajenos fuera de su rol.

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
