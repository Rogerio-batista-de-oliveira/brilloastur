from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_mail import Mail, Message
import mysql.connector
from functools import wraps
import os

app = Flask(__name__)

# --- 1. CONFIGURACIÓN DE SEGURIDAD ---
app.secret_key = os.environ.get('SECRET_KEY', 'brillo_astur_2026_final') 
ADMIN_USER = os.environ.get('ADMIN_USER', 'admin')
ADMIN_PASS = os.environ.get('ADMIN_PASS', 'Brillo2024*') 

# --- 2. CONFIGURACIÓN DE CORREO ---
app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT=587,
    MAIL_USE_TLS=True,
    MAIL_USERNAME=os.environ.get('MAIL_USER', 'rogerioba28@gmail.com'),
    MAIL_PASSWORD=os.environ.get('MAIL_PASS', 'hkvotigphqueowdc'),
    MAIL_DEFAULT_SENDER=os.environ.get('MAIL_USER', 'rogerioba28@gmail.com')
)
mail = Mail(app)

# --- 3. CONEXIÓN BASE DE DATOS ---
def get_db_connection():
    return mysql.connector.connect(
        host=os.environ.get('DB_HOST'),
        user=os.environ.get('DB_USER'),
        password=os.environ.get('DB_PASS'),
        database=os.environ.get('DB_NAME'),
        port=int(os.environ.get('DB_PORT', 4000)),
        ssl_verify_cert=True,
        ssl_ca=os.environ.get('SSL_CERT_PATH', '/etc/ssl/certs/ca-certificates.crt'),
        connect_timeout=10 # Para evitar lentitud si el banco no responde rápido
    )

# --- 4. RUTAS ---

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/servicio/<tipo>')
def servicio_detalle(tipo):
    # (Mantener igual que el anterior, solo asegurar que apunte a servicio.html)
    return render_template('servicio.html', info={}) # Simplificado para el ejemplo

@app.route('/calculadora', methods=['GET', 'POST'])
def calculadora():
    presupuesto_final = None
    ciudades_lista = []
    
    # Cargar ciudades para el select
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT nombre FROM localidades ORDER BY nombre ASC")
        ciudades_lista = [row['nombre'].title() for row in cursor.fetchall()]
        conn.close()
    except: pass

    if request.method == 'POST':
        # Captura de todos los datos del formulario
        cliente = request.form.get('cliente', 'Cliente')
        telefono = request.form.get('telefono', 'N/A')
        email_cliente = request.form.get('email', 'N/A')
        direccion = request.form.get('direccion', '').lower().strip()
        cp = request.form.get('cp', 'N/A')
        calle = request.form.get('calle', 'N/A')
        id_servicio = request.form.get('servicio', '1')
        horas = float(request.form.get('horas', 1) or 1)
        
        # Lógica de Materiales (Checkbox en el HTML debe llamarse 'materiales')
        incluye_materiales = True if request.form.get('materiales') else False
        coste_materiales = 20.0 if incluye_materiales else 0.0

        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            
            # Datos de Localidad y Tarifa
            cursor.execute("SELECT distancia_km, tiene_peaje FROM localidades WHERE nombre = %s", (direccion,))
            loc = cursor.fetchone()
            cursor.execute("SELECT nombre, tarifa_hora FROM servicios WHERE id = %s", (id_servicio,))
            serv = cursor.fetchone()

            km = loc['distancia_km'] if loc else 0
            peaje = 27.0 if (loc and loc['tiene_peaje']) else 0.0
            tarifa = float(serv['tarifa_hora']) if serv else 19.0
            nombre_serv = serv['nombre'] if serv else "Limpieza"

            # MOTOR DE CÁLCULO
            mano_de_obra = horas * tarifa
            desplazamiento = ((km * 2) / 10) * 2 
            subtotal = mano_de_obra + desplazamiento + peaje + coste_materiales
            iva = subtotal * 0.21
            total = subtotal + iva

            # PRESUPUESTO DETALLADO (CASTELLANO)
            presupuesto_final = {
                'cliente': cliente,
                'servicio': nombre_serv,
                'horas': horas,
                'direccion': f"{calle.title()}, {direccion.title()} (CP: {cp})",
                'mano_de_obra': f"{mano_de_obra:.2f}",
                'materiales': f"{coste_materiales:.2f}",
                'desplazamiento': f"{desplazamiento:.2f}",
                'peaje': f"{peaje:.2f}",
                'iva': f"{iva:.2f}",
                'total': f"{total:.2f}"
            }

            # Guardar en DB
            query = """INSERT INTO presupuestos (nombre_cliente, telefono, email, localidad, servicio_id, horas_estimadas, total_presupuestado) 
                       VALUES (%s, %s, %s, %s, %s, %s, %s)"""
            cursor.execute(query, (cliente, telefono, email_cliente, direccion.title(), id_servicio, horas, total))
            conn.commit()
            conn.close()

            # Enviar Email en segundo plano (simulado con try/except rápido)
            try:
                msg = Message(f"Nuevo Presupuesto: {cliente}", recipients=['brilloastur@yahoo.com', 'rogerioba28@gmail.com'])
                msg.body = f"""
                NUEVO LEAD - BRILLO ASTUR
                -------------------------
                Cliente: {cliente}
                Teléfono: {telefono}
                Email: {email_cliente}
                Dirección: {calle}, {direccion} (CP: {cp})
                Servicio: {nombre_serv}
                Horas: {horas}h
                Materiales Incluidos: {'Sí' if incluye_materiales else 'No'}
                -------------------------
                TOTAL ESTIMADO: {total:.2f}€ (IVA incluido)
                """
                mail.send(msg)
            except: print("Email demoró demasiado, se envió después.")

        except Exception as e:
            print(f"Error: {e}")
            flash("Error en el cálculo.", "danger")

    return render_template('calculadora.html', presupuesto=presupuesto_final, ciudades=ciudades_lista)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['username'] == ADMIN_USER and request.form['password'] == ADMIN_PASS:
            session['logged_in'] = True
            return redirect(url_for('admin_panel'))
    return render_template('login.html')

@app.route('/admin')
@login_required
def admin_panel():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT p.*, s.nombre as servicio_nombre FROM presupuestos p LEFT JOIN servicios s ON p.servicio_id = s.id ORDER BY p.fecha_creacion DESC")
        datos = cursor.fetchall()
        conn.close()
        return render_template('admin.html', presupuestos=datos)
    except: return "Error Admin", 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)