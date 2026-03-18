# 🧼 Brillo Astur - Plataforma de Gestión de Limpieza Profesional

![Estado](https://img.shields.io/badge/Estado-Producción-green?style=for-the-badge)
![Tecnología](https://img.shields.io/badge/Tecnología-Flask_%7C_MySQL_%7C_Bootstrap_5-blue?style=for-the-badge)
![Deploy](https://img.shields.io/badge/Deploy-Render-informational?style=for-the-badge)

**Brillo Astur** es una solución web integral diseñada para servicios de limpieza avanzada con sede en **Mieres, Asturias**. El sistema combina una estética corporativa elegante con herramientas interactivas de alta precisión para la captación y gestión de clientes.

---

## 🚀 Funcionalidades Principales

### 🧮 1. Motor de Cálculo Lógico (Business Logic)
El núcleo del sistema procesa múltiples variables para ofrecer un presupuesto transparente y exacto:
* **Desglose Detallado:** Calcula mano de obra, suplemento de materiales profesionales (**20,00€**) e IVA (21%).
* **Logística Automatizada:** Calcula el desplazamiento dinámico desde Mieres. Si la ruta atraviesa el peaje del Huerna (AP-66), el sistema añade automáticamente los **27,00€** correspondientes.
* **Interfaz Dinámica:** Los resultados se presentan mediante un Modal interactivo con opción de impresión profesional.

### 📍 2. Validación de Ubicación y Servicios
* **Validación en Tiempo Real:** Mediante JavaScript y la API de *Nominatim*, el sistema valida el Código Postal y autocompleta la localidad.
* **Rutas Dinámicas:** Páginas específicas para `Hogar` y `Fin de Obra` que adaptan el contenido según la necesidad técnica del cliente.

### 🔐 3. Panel de Gestión Administrativa (Backoffice)
* **Control de Leads:** Entorno protegido mediante `@login_required` donde el administrador gestiona los presupuestos recibidos.
* **Integración WhatsApp:** Enlace directo para contactar al cliente con un solo clic desde la tabla de gestión.
* **Notificaciones:** Envío automático de alertas por correo electrónico mediante **Flask-Mail** (SMTP).

---

## 🚀 Infraestructura y Despliegue (DevOps)
Esta sección detalla el flujo de trabajo técnico y la arquitectura de nube utilizada para garantizar que **Brillo Astur** sea una plataforma escalable y segura.

### ☁️ 1. Arquitectura de Datos (TiDB Cloud)
En lugar de una base de datos local, el proyecto utiliza **TiDB Cloud**, una base de datos SQL distribuida de última generación con compatibilidad MySQL.
* **Conexión Segura:** Implementación de túneles **SSL/TLS** mediante certificados de CA (`isrgrootx1.pem`) para proteger la integridad de los datos de los clientes en tránsito.
* **Escalabilidad:** Arquitectura preparada para soportar picos de tráfico sin pérdida de rendimiento.

### 🛠️ 2. Pipeline de Despliegue (Git & Render)
Se ha implementado un flujo de **Integración Continua (CI/CD)**:
* **Control de Versiones (Git/GitHub):** Gestión de código mediante ramas, asegurando que cada cambio sea registrado y reversible.
* **Deploy Automatizado en Render:** Conexión directa entre el repositorio de GitHub y los servidores de Render. Cada `git push origin main` dispara automáticamente:
    1. La reconstrucción del entorno virtual de Python.
    2. La instalación de dependencias mediante `requirements.txt`.
    3. El reinicio del servidor **Gunicorn** para aplicar cambios sin tiempo de inactividad.

---

## 📂 Estructura del Repositorio

```text
/brillo-astur
│
├── app.py                # Servidor Flask y motor de cálculo
├── requirements.txt      # Dependencias del sistema
├── static/               # CSS, JS y Multimedia (Video/Imágenes)
├── templates/            # Vistas Jinja2
│   ├── layout.html       # Estructura global y Navbar
│   ├── home.html         # Landing page
│   ├── calculadora.html  # Interfaz del presupuesto detallado
│   ├── servicio.html     # Página dinámica de servicios
│   ├── admin.html        # Panel de gestión
│   └── login.html        # Acceso administrativo
└── README.md             # Documentación técnica