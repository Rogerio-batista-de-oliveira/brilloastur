from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_mail import Mail, Message
import mysql.connector
from functools import wraps
import os
import threading

app = Flask(__name__)

# --- 1. CONFIGURACIÓN DE SEGURIDAD ---
app.secret_key = os.environ.get('SECRET_KEY', 'brillo_astur_secret_key_2026') 
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

def send_async_email(app, msg):
    with app.app_context():
        try:
            mail.send(msg)
        except Exception as e:
            print(f"Error email: {e}")

# --- 3. CONEXIÓN BASE DE DATOS ---
def get_db_connection():
    return mysql.connector.connect(
        host=os.environ.get('DB_HOST'),
        user=os.environ.get('DB_USER'),
        password=os.environ.get('DB_PASS'),
        database=os.environ.get('DB_NAME'),
        port=int(os.environ.get('DB_PORT', 4000)),
        ssl_verify_cert=True,
        ssl_ca=os.environ.get('SSL_CERT_PATH', '/etc/ssl/certs/ca-certificates.crt')
    )

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# --- 5. RUTAS PÚBLICAS ---

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/servicio/<tipo>')
def servicio_detalle(tipo):
    servicios_info = {
        'pos-obra': {'titulo': 'Limpieza Pos-Obra', 'descripcion': 'Limpieza técnica profunda.', 'puntos': [], 'imagen': ''},
        'hogar': {'titulo': 'Mantenimiento Hogar', 'descripcion': 'Cuidado constante.', 'puntos': [], 'imagen': ''}
    }
    info = servicios_info.get(tipo)
    return render_template('servicio.html', info=info) if info else redirect(url_for('home'))

@app.route('/calculadora', methods=['GET', 'POST'])
def calculadora():
    presupuesto_final = None
    ciudades_lista = []
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT nombre FROM localidades ORDER BY nombre ASC")
        ciudades_lista = [row['nombre'].title() for row in cursor.fetchall()]
        conn.close()
    except: pass

    if request.method == 'POST':
        try:
            cliente = request.form.get('cliente')
            telefono = request.form.get('telefono')
            email_cliente = request.form.get('email')
            direccion_raw = request.form.get('direccion', '').lower().strip()
            ciudad_para_busca = direccion_raw.split(',')[0].strip()
            opcion_servicio = request.form.get('servicio', '1')
            horas = float(request.form.get('horas', 1))
            coste_materiales = 20.0 if request.form.get('materiales') else 0.0

            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT distancia_km, tiene_peaje FROM localidades WHERE nombre = %s", (ciudad_para_busca,))
            loc = cursor.fetchone()
            cursor.execute("SELECT nombre, tarifa_hora FROM servicios WHERE id = %s", (opcion_servicio,))
            serv = cursor.fetchone()

            km, peaje = (loc['distancia_km'], 27.0 if loc['tiene_peaje'] else 0.0) if loc else (0, 0)
            tarifa, nombre_serv = (float(serv['tarifa_hora']), serv['nombre']) if serv else (19.0, "Limpieza")

            total = ((horas * tarifa) + (((km * 2) / 10) * 2) + peaje + coste_materiales) * 1.21

            presupuesto_final = {'cliente': cliente, 'total': f"{total:.2f}", 'servicio': nombre_serv} # Simplificado para el ejemplo

            cursor.execute("INSERT INTO presupuestos (nombre_cliente, telefono, email, localidad, servicio_id, horas_estimadas, total_presupuestado) VALUES (%s, %s, %s, %s, %s, %s, %s)", 
                           (cliente, telefono, email_cliente, ciudad_para_busca.title(), opcion_servicio, horas, total))
            conn.commit()
            conn.close()

            msg = Message(f"Nuevo Lead: {cliente}", recipients=['brilloastur@yahoo.com'])
            msg.body = f"Presupuesto de {total:.2f}€"
            threading.Thread(target=send_async_email, args=(app, msg)).start()
        except Exception as e: flash(f"Error: {e}", "danger")

    return render_template('calculadora.html', presupuesto=presupuesto_final, ciudades=ciudades_lista)

# --- 6. ADMINISTRACIÓN ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['username'] == ADMIN_USER and request.form['password'] == ADMIN_PASS:
            session['logged_in'] = True
            return redirect(url_for('admin_panel'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

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
    except Exception as e: return f"Error: {e}", 500

# MODIFICACIÓN CRÍTICA: Añadido 'GET' para que la papelera funcione como enlace directo
@app.route('/eliminar_presupuesto/<int:id>', methods=['GET', 'POST'])
@login_required
def eliminar_presupuesto(id):
    try:
        conn = get_db_connection()
        cursor = conn.close() # Reset
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM presupuestos WHERE id = %s", (id,))
        conn.commit()
        conn.close()
        flash("Presupuesto eliminado correctamente", "success")
    except Exception as e:
        flash(f"Error al eliminar: {e}", "danger")
    return redirect(url_for('admin_panel'))

@app.route('/actualizar_estatus/<int:id>', methods=['GET', 'POST'])
@login_required
def actualizar_estatus(id):
    nuevo_estatus = request.form.get('estatus') or request.args.get('estatus')
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE presupuestos SET estatus = %s WHERE id = %s", (nuevo_estatus, id))
        conn.commit()
        conn.close()
    except: pass
    return redirect(url_for('admin_panel'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))