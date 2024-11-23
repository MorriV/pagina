from flask import Flask, render_template, request, redirect, url_for, session
from functools import wraps
from datetime import timedelta
import sqlite3

# Configuración de la aplicación Flask
app = Flask(__name__)
app.secret_key = 'clave_secreta_para_sesiones'  # Clave secreta para las sesiones
app.permanent_session_lifetime = timedelta(minutes=30)  # Duración de la sesión: 30 minutos de inactividad

# Función para conectarse a la base de datos SQLite
def get_db_connection():
    conn = sqlite3.connect('elevadores.db')
    conn.row_factory = sqlite3.Row  # Permite acceder a las columnas por nombre
    return conn

# Decorador para proteger rutas
def login_required(role=None):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if 'user_id' not in session:
                return redirect('/')
            if role and session.get('role') != role:
                return redirect('/')
            return func(*args, **kwargs)
        return wrapper
    return decorator

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    usuario = request.form['usuario']
    password = request.form['password']

    conn = get_db_connection()
    user = conn.execute('SELECT * FROM usuarios WHERE nombre_usuario = ? AND contraseña = ?', (usuario, password)).fetchone()
    conn.close()

    if user:
        session.permanent = True
        session['user_id'] = user['id_usuario']
        session['username'] = user['nombre_usuario']
        session['role'] = user['rol']

        if user['rol'] == 'administrador':
            return redirect('/apdc')
        elif user['rol'] == 'tecnico':
            return redirect('/pdc')
    return render_template('index.html', error="Usuario o contraseña incorrectos")

@app.route('/apdc')
@login_required(role='administrador')
def admin_panel():
    conn = get_db_connection()
    reports = conn.execute('''
        SELECT * FROM reportes
    ''').fetchall()
    acciones_admin = conn.execute('''
        SELECT * FROM acciones_admin
    ''').fetchall()
    conn.close()
    return render_template(
        'apdc.html',
        reports=[dict(row) for row in reports],
        acciones_admin=[dict(row) for row in acciones_admin]
    )

@app.route('/editar_reporte/<int:id_reporte>', methods=['GET', 'POST'])
@login_required(role='administrador')
def editar_reporte(id_reporte):
    conn = get_db_connection()

    # Definir listas de checkboxes para bloques y puntos
    bloques = [
        "reparacion", "mantenimiento", "falla_averia", "fallas_24_7", "emergencia_24_7",
        "diagnostico_tecnico", "traslado_logistica", "levantamiento_datos_tecnicos",
        "modernizacion", "montaje_nuevo"
    ]
    puntos = [
        "micro_inf_final", "micro_sup_final", "stop_foso", "micro_lim_vel", "micro_acunamiento",
        "micro_polea_tensora", "micro_puertas_cab", "micro_puertas_ext", "stop_techo_cabina"
    ]

    if request.method == 'POST':
        # Capturar datos enviados desde el formulario
        cliente = request.form['cliente']
        direccion = request.form['direccion']
        equipo = request.form['equipo']
        fecha = request.form['fecha']
        bloque_mantenimiento = request.form['bloque_mantenimiento']
        cie = request.form['cie']
        resumen_actividad = request.form['resumen']
        refaccion = request.form['refaccion']
        equipo_parado = 1 if request.form.get('equipo_parado') == 'Sí' else 0
        equipo_funcionando = 1 if request.form.get('equipo_funcionando') == 'Sí' else 0

        # Preparar valores de checkboxes
        valores_bloques = {bloque: 1 if bloque in request.form else 0 for bloque in bloques}
        valores_puntos = {punto: 1 if punto in request.form else 0 for punto in puntos}

        # Actualizar el reporte en la base de datos
        conn.execute(f'''
            UPDATE reportes
            SET cliente = ?, direccion = ?, equipo = ?, fecha = ?, bloque_mantenimiento_momb = ?,
                cie = ?, resumen_actividad = ?, refaccion_componente = ?, equipo_parado = ?, 
                equipo_funcionando = ?, {", ".join(f"{k} = ?" for k in valores_bloques.keys())},
                {", ".join(f"{k} = ?" for k in valores_puntos.keys())}
            WHERE id_reporte = ?
        ''', (
            cliente, direccion, equipo, fecha, bloque_mantenimiento, cie, resumen_actividad,
            refaccion, equipo_parado, equipo_funcionando, *valores_bloques.values(),
            *valores_puntos.values(), id_reporte
        ))

        # Registrar la acción en `acciones_admin`
        conn.execute('''
            INSERT INTO acciones_admin (id_reporte, id_usuario, accion, fecha_accion)
            VALUES (?, ?, ?, datetime('now'))
        ''', (id_reporte, session['user_id'], 'editar'))

        conn.commit()
        conn.close()

        return redirect('/apdc')  # Redirigir al panel del administrador

    else:
        # Obtener datos actuales del reporte
        reporte = conn.execute('SELECT * FROM reportes WHERE id_reporte = ?', (id_reporte,)).fetchone()

        if not reporte:
            conn.close()
            return "Reporte no encontrado", 404

        # Preparar valores para checkboxes
        valores_bloques = {bloque: reporte[bloque] for bloque in bloques}
        valores_puntos = {punto: reporte[punto] for punto in puntos}

        conn.close()
        return render_template('editar_reporte.html', reporte=dict(reporte), bloques=valores_bloques, puntos=valores_puntos)

@app.route('/eliminar_reporte/<int:id_reporte>', methods=['DELETE'])
@login_required(role='administrador')
def eliminar_reporte(id_reporte):
    conn = get_db_connection()
    conn.execute('DELETE FROM reportes WHERE id_reporte = ?', (id_reporte,))
    conn.execute('''
        INSERT INTO acciones_admin (id_reporte, id_usuario, accion, fecha_accion)
        VALUES (?, ?, ?, datetime('now'))
    ''', (id_reporte, session['user_id'], 'eliminar'))
    conn.commit()
    conn.close()
    return '', 204

@app.route('/pdc')
@login_required(role='tecnico')
def tecnico_panel():
    return render_template('pdc.html')

@app.route('/levantar_reporte', methods=['GET', 'POST'])
@login_required(role='tecnico')
def levantar_reporte():
    if request.method == 'POST':
        # Manejo de reportes levantados
        pass
    return render_template('levantar_reporte.html')

@app.route('/ver_reportes')
@login_required(role='tecnico')
def ver_reportes():
    conn = get_db_connection()
    reports = conn.execute('SELECT * FROM reportes WHERE id_usuario = ?', (session['user_id'],)).fetchall()
    conn.close()
    return render_template('ver_reportes.html', reports=[dict(row) for row in reports])

if __name__ == '__main__':
    app.run(debug=True)
