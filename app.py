from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_mail import Mail, Message
import mysql.connector
from functools import wraps
import os

app = Flask(__name__)

# --- CONFIGURACIÓN DE SEGURIDAD ---
# Se obtienen de las variables de entorno de Render para mayor seguridad
app.secret_key = os.environ.get('SECRET_KEY', 'brillo_astur_secret_key_2024') 
ADMIN_USER = os.environ.get('ADMIN_USER', 'admin')
ADMIN_PASS = os.environ.get('ADMIN_PASS', 'Brillo2024*') 

# --- CONFIGURACIÓN DE CORREO (Gmail) ---
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USER', 'rogerioba28@gmail.com')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASS', 'hkvotigphqueowdc')  
app.config['MAIL_DEFAULT_SENDER'] = app.config['MAIL_USERNAME']
mail = Mail(app)

# --- FUNCIÓN CONEXIÓN BASE DE DATOS (Configurada para TiDB Cloud) ---
def get_db_connection():
    return mysql.connector.connect(
        host=os.environ.get('DB_HOST', 'localhost'),
        user=os.environ.get('DB_USER', 'root'),
        password=os.environ.get('DB_PASS', ''),
        database=os.environ.get('DB_NAME', 'brilloastur_db'),
        port=int(os.environ.get('DB_PORT', 4000)),
        # 🛡️ IMPORTANTE PARA TiDB CLOUD: Conexión segura SSL
        ssl_verify_cert=True,
        ssl_ca=os.environ.get('SSL_CERT_PATH', '/etc/ssl/certs/ca-certificates.crt')
    )

# --- DECORADOR PARA PROTEGER EL PANEL ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# --- RUTAS DE GESTIÓN ---

@app.route('/eliminar_presupuesto/<int:id>')
@login_required
def eliminar_presupuesto(id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM presupuestos WHERE id = %s", (id,))
        conn.commit()
        conn.close()
        flash(f'Presupuesto #{id} eliminado.', 'warning')
    except Exception as e:
        print(f"❌ Error: {e}")
        flash('No se pudo eliminar.', 'danger')
    return redirect(url_for('admin_panel'))

# --- RUTAS PÚBLICAS ---

@app.route('/')
def home():
    return render_template('home.html')

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
    except Exception as e:
        print(f"⚠️ Error de BD al cargar ciudades: {e}")

    if request.method == 'POST':
        cliente = request.form.get('cliente', 'Cliente')
        telefono = request.form.get('telefono', 'No proporcionado')
        email_cliente = request.form.get('email', 'No proporcionado')
        cp = request.form.get('cp', '')
        calle = request.form.get('calle', '')
        numero = request.form.get('numero', '')
        piso = request.form.get('piso', '')
        direccion_input = request.form.get('direccion', '').lower().strip()
        opcion_servicio = request.form.get('servicio', '1')
        
        try:
            horas = float(request.form.get('horas', 1) or 1)
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            
            cursor.execute("SELECT distancia_km, tiene_peaje FROM localidades WHERE nombre = %s", (direccion_input,))
            loc_data = cursor.fetchone()
            
            cursor.execute("SELECT nombre, tarifa_hora FROM servicios WHERE id = %s", (opcion_servicio,))
            serv_data = cursor.fetchone()
            conn.close()

            km_ida = loc_data['distancia_km'] if loc_data else 0
            total_peajes = 27.00 if (loc_data and loc_data['tiene_peaje']) else 0.0
            nombre_serv = serv_data['nombre'] if serv_data else "Servicio"
            precio_hora = float(serv_data['tarifa_hora']) if serv_data else 19.0

            mano_de_obra = horas * precio_hora
            coste_desplazamiento = ((km_ida * 2) / 10) * 2 
            subtotal = mano_de_obra + coste_desplazamiento + total_peajes
            iva = subtotal * 0.21
            total = subtotal + iva

            presupuesto_final = (
                f"✨ BRILLO ASTUR - PRESUPUESTO ✨\n\n"
                f"👤 CLIENTE: {cliente}\n"
                f"📞 TEL: {telefono}\n"
                f"📍 DIRECCIÓN: {calle}, {numero} {piso} - {cp}\n"
                f"🛠 SERVICIO: {nombre_serv}\n"
                f"⏱ HORAS: {horas}h\n"
                f"💰 TOTAL: {total:.2f}€ (IVA incl.)"
            )

            conn = get_db_connection()
            cursor = conn.cursor()
            query = """
                INSERT INTO presupuestos (
                    nombre_cliente, telefono, email, cp, calle, 
                    numero, piso, localidad, 
                    servicio_id, horas_estimadas, total_presupuestado
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            valores = (cliente, telefono, email_cliente, cp, calle, numero, piso, 
                       direccion_input.title(), opcion_servicio, horas, total)
            cursor.execute(query, valores)
            conn.commit()
            conn.close()

            msg = Message(subject=f"Nuevo Lead: {cliente}", recipients=['brilloastur@yahoo.com', 'rogerioba28@gmail.com'])
            msg.body = presupuesto_final
            mail.send(msg)

        except Exception as e:
            print(f"❌ Error en el proceso: {e}")
            flash("Hubo un error al calcular el presupuesto.", "danger")

    return render_template('calculadora.html', presupuesto=presupuesto_final, ciudades=ciudades_lista)

@app.route('/servicio/<tipo>')
def servicio_detalle(tipo):
    servicios_info = {
        'pos-obra': {
            'titulo': 'Limpieza Pos-Obra',
            'descripcion': 'Limpieza técnica profunda tras reformas.',
            'puntos': ['Maquinaria profesional', 'Eliminación de restos', 'Cristales e suelos'],
            'imagen': 'https://images.unsplash.com/photo-1584622650111-993a426fbf0a?w=800'
        },
        'hogar': {
            'titulo': 'Mantenimiento Hogar',
            'descripcion': 'Brillo y confianza para tu casa.',
            'puntos': ['Limpieza semanal', 'Desinfección total', 'Personal cualificado'],
            'imagen': 'https://images.unsplash.com/photo-1527515637462-cff94eecc1ac?w=800'
        }
    }
    info = servicios_info.get(tipo)
    if not info:
        return "Servicio no encontrado", 404
    return render_template('servicio.html', info=info)

# --- RUTAS DE ADMINISTRACIÓN ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['username'] == ADMIN_USER and request.form['password'] == ADMIN_PASS:
            session['logged_in'] = True
            return redirect(url_for('admin_panel'))
        else:
            flash('Usuario o contraseña incorrectos', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route('/admin')
@login_required
def admin_panel():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT p.*, s.nombre as servicio_nombre 
        FROM presupuestos p 
        LEFT JOIN servicios s ON p.servicio_id = s.id 
        ORDER BY p.fecha_creacion DESC
    """)
    datos = cursor.fetchall()
    conn.close()
    return render_template('admin.html', presupuestos=datos)

@app.route('/actualizar_estatus/<int:id>')
@login_required
def actualizar_estatus(id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE presupuestos SET estatus = 'contactado' WHERE id = %s", (id,))
        conn.commit()
        conn.close()
        flash(f'Presupuesto #{id} actualizado ✅', 'success')
    except Exception as e:
        print(f"❌ Error: {e}")
        flash('No se pudo actualizar el estado', 'danger')
    return redirect(url_for('admin_panel'))

if __name__ == '__main__':
    # Puerto dinámico para Render
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)