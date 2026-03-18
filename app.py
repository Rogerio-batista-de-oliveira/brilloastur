from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_mail import Mail, Message
import mysql.connector
from functools import wraps
import os

app = Flask(__name__)

# --- 1. CONFIGURACIÓN DE SEGURIDAD ---
app.secret_key = os.environ.get('SECRET_KEY', 'brillo_astur_prod_2026') 
ADMIN_USER = os.environ.get('ADMIN_USER', 'admin')
ADMIN_PASS = os.environ.get('ADMIN_PASS', 'Brillo2024*') 

# --- 2. CONFIGURACIÓN DE CORREO (Gmail) ---
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USER', 'rogerioba28@gmail.com')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASS', 'hkvotigphqueowdc')
app.config['MAIL_DEFAULT_SENDER'] = app.config['MAIL_USERNAME']
# Timeout para o e-mail não travar o site
app.config['MAIL_TIMEOUT'] = 10 

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
        ssl_ca=os.environ.get('SSL_CERT_PATH', '/etc/ssl/certs/ca-certificates.crt')
    )

# --- 4. DECORADOR ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# --- 5. RUTAS ---

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/servicio/<tipo>')
def servicio_detalle(tipo):
    servicios_info = {
        'pos-obra': {
            'titulo': 'Limpieza Pos-Obra',
            'descripcion': 'Limpieza técnica profunda tras reformas o construcción.',
            'puntos': ['Eliminación de polvo fino', 'Limpieza de cristales y marcos', 'Desinfección de superficies'],
            'imagen': 'https://images.unsplash.com/photo-1584622650111-993a426fbf0a?w=800'
        },
        'hogar': {
            'titulo': 'Mantenimiento Hogar',
            'descripcion': 'Cuidado constante y detallado para tu casa en Asturias.',
            'puntos': ['Limpieza de cocina y baños', 'Aspirado y fregado profesional', 'Orden y desinfección'],
            'imagen': 'https://images.unsplash.com/photo-1527515637462-cff94eecc1ac?w=800'
        }
    }
    info = servicios_info.get(tipo)
    if not info: return redirect(url_for('home'))
    return render_template('servicio.html', info=info)

@app.route('/calculadora', methods=['GET', 'POST'])
def calculadora():
    presupuesto_final = None
    ciudades_lista = []
    
    # Carregar cidades
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT nombre FROM localidades ORDER BY nombre ASC")
        ciudades_lista = [row['nombre'].title() for row in cursor.fetchall()]
    except Exception as e:
        print(f"Error ciudades: {e}")
    finally:
        if conn and conn.is_connected(): conn.close()

    if request.method == 'POST':
        cliente = request.form.get('cliente', 'Cliente')
        telefono = request.form.get('telefono', 'N/A')
        email_cliente = request.form.get('email', 'N/A')
        direccion_input = request.form.get('direccion', '').lower().strip()
        opcion_servicio = request.form.get('servicio', '1')
        horas = float(request.form.get('horas', 1) or 1)
        
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            
            # Buscar dados
            cursor.execute("SELECT distancia_km, tiene_peaje FROM localidades WHERE nombre = %s", (direccion_input,))
            loc_data = cursor.fetchone()
            cursor.execute("SELECT nombre, tarifa_hora FROM servicios WHERE id = %s", (opcion_servicio,))
            serv_data = cursor.fetchone()

            km = loc_data['distancia_km'] if loc_data else 0
            peaje = 27.00 if (loc_data and loc_data['tiene_peaje']) else 0.0
            tarifa = float(serv_data['tarifa_hora']) if serv_data else 19.0

            # Cálculo
            subtotal = (horas * tarifa) + (((km * 2) / 10) * 2) + peaje
            total = subtotal * 1.21

            presupuesto_final = f"✨ BRILLO ASTUR ✨\nCliente: {cliente}\nTotal: {total:.2f}€"

            # Salvar no Banco
            query = "INSERT INTO presupuestos (nombre_cliente, telefono, email, localidad, servicio_id, horas_estimadas, total_presupuestado) VALUES (%s, %s, %s, %s, %s, %s, %s)"
            cursor.execute(query, (cliente, telefono, email_cliente, direccion_input.title(), opcion_servicio, horas, total))
            conn.commit()

            # Enviar E-mail (Protegido)
            try:
                msg = Message(f"Nuevo Lead: {cliente}", recipients=['brilloastur@yahoo.com', 'rogerioba28@gmail.com'])
                msg.body = f"Nuevo presupuesto generado:\n\n{presupuesto_final}"
                mail.send(msg)
            except:
                print("⚠️ E-mail falhou, mas orçamento foi salvo.")

        except Exception as e:
            print(f"❌ Erro Crítico: {e}")
            flash("Error al procesar. Intente de nuevo.", "danger")
        finally:
            if conn and conn.is_connected(): conn.close()

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
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT p.*, s.nombre as servicio_nombre FROM presupuestos p LEFT JOIN servicios s ON p.servicio_id = s.id ORDER BY p.fecha_creacion DESC")
        datos = cursor.fetchall()
        return render_template('admin.html', presupuestos=datos)
    except:
        return "Error BD", 500
    finally:
        if conn and conn.is_connected(): conn.close()

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)