# 🧼 Brillo Astur - Plataforma de Gestión de Limpieza Profesional

![Estado](https://img.shields.io/badge/Estado-En_Desarrollo-green?style=for-the-badge)
![Tecnología](https://img.shields.io/badge/Tecnología-Flask_%7C_MySQL_%7C_Bootstrap_5-blue?style=for-the-badge)
![Licencia](https://img.shields.io/badge/Licencia-MIT-orange?style=for-the-badge)

**Brillo Astur** es una solución web integral diseñada para servicios de limpieza avanzada con sede en **Mieres, Asturias**. El proyecto combina una estética corporativa elegante con herramientas interactivas de alta precisión para la captación y conversión de clientes.

---

## 🛠️ Propósito y Estrategia
El sitio ha sido desarrollado para profesionalizar y agilizar la contratación de servicios de limpieza en el Principado de Asturias. Se enfoca en la transparencia de precios y en ofrecer una narrativa de venta persuasiva que destaca la calidad técnica sobre la competencia convencional.

### Especialidades:
* **Limpieza de Fin de Obra:** Eliminación técnica de residuos de construcción y polvo fino. 🏗️
* **Mantenimiento del Hogar:** Gestión de limpieza recurrente basada en la confianza y el detalle. 🏠

---

## 🚀 Funcionalidades Principales Implantadas

### 📍 1. Validación de Ubicación y Geocodificación Inteligente
Esta funcionalidad elimina la fricción en el formulario y garantiza que los cálculos logísticos sean precisos desde el primer contacto.
* **Validación en Tiempo Real:** Mediante JavaScript, el sistema realiza llamadas asíncronas a la API de *Nominatim* al introducir el Código Postal (CP).
* **Gestión de Errores (UX):** Si el CP es inexistente, el sistema dispara una alerta visual inmediata ⚠️, guiando al usuario para corregir los datos antes del envío.
* **Autocompletado:** Identifica automáticamente concejos y localidades, bloqueando los datos para que el Backend reciba información verificada.

### 🧮 2. Motor de Cálculo Lógico (Business Logic)
El núcleo del sistema procesa múltiples variables para ofrecer un presupuesto transparente y exacto.
* **Algoritmo de Costes:** Suma el coste base, horas estimadas y suplementos por materiales industriales.
* **Logística Automatizada:** Calcula el desplazamiento desde Mieres. Si la ruta atraviesa el peaje del Huerna (AP-66), el sistema añade automáticamente dicho coste al presupuesto. 🛣️
* **Resultados Dinámicos:** Muestra el desglose final (incluyendo IVA) a través de un Modal interactivo, facilitando la conversión inmediata.

### 🔐 3. Panel de Gestión Administrativa (Backoffice)
Un entorno restringido para transformar los "leads" en clientes reales mediante una gestión organizada y segura.
* **Seguridad de Acceso:** Uso de decoradores `@login_required` y gestión de sesiones para proteger los datos de los clientes. 🛡️
* **Control de Estados:** El administrador puede visualizar los detalles y marcar cada presupuesto como "Contactado" para un seguimiento comercial eficiente.
* **Gestión de Registros (CRUD):** Funcionalidad completa para revisar y eliminar registros obsoletos, manteniendo la base de datos MySQL optimizada. 🗑️

---

## 💻 Stack Tecnológico

* **Backend:** [Flask](https://flask.palletsprojects.com/) (Python) para procesamiento de datos y rutas dinámicas.
* **Base de Datos:** [MySQL](https://www.mysql.com/) para la persistencia de servicios, localidades y presupuestos.
* **Frontend:** [Bootstrap 5](https://getbootstrap.com/) para diseño responsivo y componentes UI.
* **Notificaciones:** Integración SMTP para alertas de nuevos presupuestos en tiempo real. 📧

---

## 📂 Estructura del Repositorio

```text
/brillo-astur
│
├── app.py                # Servidor Flask y lógica de la calculadora
├── static/               # Recursos estáticos (CSS, Video, Imágenes)
├── templates/            # Vistas HTML (Jinja2)
│   ├── layout.html       # Estructura global (Header/Footer/Scripts)
│   ├── home.html         # Landing page principal
│   ├── admin.html        # Panel de gestión de presupuestos
│   └── calculadora.html  # Interfaz del presupuesto online
└── README.md             # Documentación técnica y estratégica