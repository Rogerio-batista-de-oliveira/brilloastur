# 🧼 Brillo Astur - Plataforma de Gestión de Limpieza Profesional

![Estado](https://img.shields.io/badge/Estado-Producción-green?style=for-the-badge)
![Tecnología](https://img.shields.io/badge/Tecnología-Flask_%7C_MySQL_%7C_Bootstrap_5-blue?style=for-the-badge)

**Brillo Astur** es una solución web integral diseñada para servicios de limpieza avanzada con sede en **Mieres, Asturias**. El sistema automatiza la captación de clientes mediante un motor de presupuestos inteligente y un panel de control administrativo.

---

## 🚀 Funcionalidades Actualizadas

### 🧮 1. Motor de Cálculo Detallado (Novedad)
El sistema ahora desglosa cada euro del presupuesto para ofrecer máxima transparencia al cliente asturiano:
* **Suplemento de Materiales:** Opción de añadir **20,00€** por uso de productos profesionales e industriales.
* **Logística Automatizada:** Cálculo dinámico de desplazamiento basado en kilometraje y detección automática de **Peajes del Huerna (AP-66)** para servicios entre León y Asturias. 🛣️
* **Transparencia Fiscal:** Cálculo automático de **IVA (21%)** y desglose de mano de obra.

### 📍 2. Geocodificación e Interfaz Dinámica
* **API de Nominatim:** Validación de códigos postales en tiempo real para autocompletar calles y localidades.
* **Páginas de Servicio Dinámicas:** Rutas inteligentes para `hogar` y `pos-obra` que cargan contenido específico según el interés del usuario.
* **Modal de Resultados:** Visualización del presupuesto estilo "recibo" listo para imprimir o guardar en PDF.

### 🔐 3. Backoffice Administrativo Profesional
* **Gestión de Leads:** Tabla interactiva para visualizar clientes, con acceso directo a **WhatsApp** para contacto inmediato.
* **Seguridad Robusta:** Protección de rutas mediante decoradores e integración de **Flask-Mail** para alertas instantáneas de nuevos presupuestos.

---

## 📂 Estructura del Proyecto Actualizada

```text
/brillo-astur
│
├── app.py                # Servidor Flask (Lógica, Cálculos y Mail)
├── requirements.txt      # Dependencias (Flask, Flask-Mail, MySQL, etc.)
├── templates/            
│   ├── layout.html       # Estructura base (Nav y Footer con WhatsApp)
│   ├── home.html         # Landing Page
│   ├── calculadora.html  # Motor de presupuesto con desglose
│   ├── servicio.html     # Vista dinámica de servicios (Hogar/Obra)
│   ├── admin.html        # Gestión de presupuestos y estados
│   └── login.html        # Acceso administrativo
└── static/               # Estilos y multimedia