from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_mail import Mail, Message
import mysql.connector
from functools import wraps
import os

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

# --- 4. DECORADOR DE PROTECCIÓN ---
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

# CORREÇÃO CRÍTICA: Adicionado <tipo> para que os links funcionem
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
    if not info:
        return redirect(url_for('home'))
    return render_template('servicio.html', info=info)

@app.route('/calculadora', methods=['GET', 'POST'])
def calculadora():
    presupuesto_final = None
    ciudades_lista = []
    
    # 1. Carregar lista de cidades para o formulário
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT nombre FROM localidades ORDER BY nombre ASC")
        ciudades_lista = [row['nombre'].title() for row in cursor.fetchall()]
        conn.close()
    except: pass

    if request.method == 'POST':
        cliente = request.form.get('cliente', 'Cliente')
        telefono = request.form.get('telefono', 'N/A')
        email_cliente = request.form.get('email', 'N/A')
        
        # --- LÓGICA DE LIMPEZA DE ENDEREÇO (SOLUÇÃO PARA O ERRO 0.00€) ---
        direccion_raw = request.form.get('direccion', '').lower().strip()
        # Se vier "León, Castela e Leão", pegamos apenas "león" para buscar no banco
        ciudad_para_busca = direccion_raw.split(',')[0].strip()
        
        opcion_servicio = request.form.get('servicio', '1')
        horas = float(request.form.get('horas', 1) or 1)
        
        # Checkbox de Materiales
        incluye_materiales = True if request.form.get('materiales') else False
        coste_materiales = 20.0 if incluye_materiales else 0.0

        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            
            # Buscamos os dados logísticos usando o nome limpo da cidade
            cursor.execute("SELECT distancia_km, tiene_peaje FROM localidades WHERE nombre = %s", (ciudad_para_busca,))
            loc = cursor.fetchone()
            
            # Buscamos a tarifa do serviço
            cursor.execute("SELECT nombre, tarifa_hora FROM servicios WHERE id = %s", (opcion_servicio,))
            serv = cursor.fetchone()

            # Se loc for None (cidade não encontrada), usamos 0 para não quebrar o cálculo
            km = loc['distancia_km'] if loc else 0
            peaje = 27.0 if (loc and loc['tiene_peaje']) else 0.0
            tarifa = float(serv['tarifa_hora']) if serv else 19.0
            nombre_serv = serv['nombre'] if serv else "Limpieza"

            # --- MOTOR DE CÁLCULO BRILLO ASTUR ---
            mano_de_obra = horas * tarifa
            # Fórmula: (KM ida e volta / consumo médio 10km/l) * preço combustível (2€/l aprox)
            desplazamiento = ((km * 2) / 10) * 2 
            subtotal = mano_de_obra + desplazamiento + peaje + coste_materiales
            iva = subtotal * 0.21
            total = subtotal + iva

            # DICIONÁRIO PARA O RESUMO NO HTML (Agora com valores reais!)
            presupuesto_final = {
                'cliente': cliente,
                'servicio': nombre_serv,
                'horas': horas,
                'direccion': direccion_raw.title(), # Mostramos o nome completo no recibo
                'mano_de_obra': f"{mano_de_obra:.2f}",
                'materiales': f"{coste_materiales:.2f}",
                'desplazamiento': f"{desplazamiento:.2f}",
                'peaje': f"{peaje:.2f}",
                'iva': f"{iva:.2f}",
                'total': f"{total:.2f}"
            }

            # Salvar no Banco (Usamos o nome limpo para a localidade na DB)
            query = """INSERT INTO presupuestos (nombre_cliente, telefono, email, localidad, servicio_id, horas_estimadas, total_presupuestado) 
                       VALUES (%s, %s, %s, %s, %s, %s, %s)"""
            cursor.execute(query, (cliente, telefono, email_cliente, ciudad_para_busca.title(), opcion_servicio, horas, total))
            conn.commit()
            conn.close()

            # Enviar Email de Notificação
            try:
                msg = Message(f"Nuevo Lead: {cliente}", recipients=['brilloastur@yahoo.com', 'rogerioba28@gmail.com'])
                msg.body = f"Nuevo presupuesto generado para {cliente} por un total de {total:.2f}€"
                mail.send(msg)
            except: pass

        except Exception as e:
            flash(f"Error en el servidor: {e}", "danger")

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
    except: return "Error", 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)