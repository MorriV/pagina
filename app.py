from flask import Flask, render_template, request, redirect, url_for, session, jsonify, make_response
from functools import wraps
from datetime import timedelta
from fpdf import FPDF

import sqlite3
def crear_app():
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
            elif user['rol'] == 'SARH':  # Nuevo rol para SARH
                return redirect('/sarhpdc')
        return render_template('index.html', error="Usuario o contraseña incorrectos")

    @app.route('/sarhpdc')
    @login_required(role='SARH')  # Solo accesible para SARH
    def sarh_panel():
        conn = get_db_connection()
        usuarios = conn.execute('SELECT id_usuario, nombre_usuario, rol FROM usuarios').fetchall()
        conn.close()
        return render_template('sarhpdc.html', usuarios=usuarios)

    @app.route('/crear_usuario', methods=['POST'])
    @login_required(role='SARH')
    def crear_usuario():
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        role = data.get('role')

        if not username or not password or not role:
            return "Datos incompletos", 400

        conn = get_db_connection()
        conn.execute('INSERT INTO usuarios (nombre_usuario, contraseña, rol) VALUES (?, ?, ?)', (username, password, role))
        conn.commit()
        conn.close()
        return '', 201

    @app.route('/eliminar_usuario/<int:usuario_id>', methods=['DELETE'])
    @login_required(role='SARH')
    def eliminar_usuario(usuario_id):
        conn = get_db_connection()
        conn.execute('DELETE FROM usuarios WHERE id_usuario = ?', (usuario_id,))
        conn.commit()
        conn.close()
        return '', 204


    @app.route('/apdc')
    @login_required(role='administrador')  # Solo accesible para administradores
    def admin_panel():
        return render_template('apdc.html')


    @app.route('/eliminar_ubicacion/<int:ubicacion_id>', methods=['POST'])
    @login_required(role='administrador')
    def eliminar_ubicacion(ubicacion_id):
        conn = get_db_connection()
        conn.execute('DELETE FROM ubicaciones WHERE id_ubicacion = ?', (ubicacion_id,))
        conn.commit()
        conn.close()
        return '', 204  # Retornar una respuesta vacía con código 204 (sin contenido)


    @app.route('/dar_alta_ubicacion', methods=['POST'])
    @login_required(role='administrador')
    def dar_alta_ubicacion():
        data = request.get_json()
        nombre = data.get('nombre')
        if not nombre:
            return "Nombre requerido", 400
        conn = get_db_connection()
        conn.execute('INSERT INTO ubicaciones (nombre) VALUES (?)', (nombre,))
        conn.commit()
        conn.close()
        return '', 201

    @app.route('/eliminar_cliente/<int:cliente_id>', methods=['POST'])
    @login_required(role='administrador')
    def eliminar_cliente(cliente_id):
        conn = get_db_connection()
        conn.execute('DELETE FROM clientes WHERE id_cliente = ?', (cliente_id,))
        conn.commit()
        conn.close()
        return '', 204  # Retornar una respuesta vacía con código 204 (sin contenido)


    @app.route('/dar_alta_cliente', methods=['POST'])
    @login_required(role='administrador')
    def dar_alta_cliente():
        data = request.get_json()
        nombre = data.get('nombre')
        if not nombre:
            return "Nombre requerido", 400
        conn = get_db_connection()
        conn.execute('INSERT INTO clientes (nombre) VALUES (?)', (nombre,))
        conn.commit()
        conn.close()
        return '', 201

    @app.route('/altas_bajas')
    @login_required(role='administrador')
    def altas_bajas():
        conn = get_db_connection()
        ubicaciones = conn.execute('SELECT * FROM ubicaciones').fetchall()
        clientes = conn.execute('SELECT * FROM clientes').fetchall()
        conn.close()
        return render_template('altas_bajas.html', ubicaciones=ubicaciones, clientes=clientes)




    @app.route('/descarga')
    @login_required(role='administrador')
    def descarga():
        # Renderiza la página descarga.html
        return render_template('descarga.html')

    

    @app.route('/visualizar')
    @login_required(role='administrador')
    def visualizar():
        conn = get_db_connection()
        tecnicos = conn.execute("SELECT id_usuario, nombre_usuario FROM usuarios WHERE rol = 'tecnico'").fetchall()
        conn.close()
        return render_template('visualizar.html', tecnicos=tecnicos)


    @app.route('/delete_report/<int:id_reporte>', methods=['DELETE'])
    @login_required(role='administrador')  # Solo accesible para administradores
    def delete_report(id_reporte):
        try:
            conn = get_db_connection()
            conn.execute('DELETE FROM reportes WHERE id_reporte = ?', (id_reporte,))
            conn.commit()
            conn.close()
            return '', 204  # Respuesta sin contenido (éxito)
        except Exception as e:
            print(f"Error al eliminar el reporte: {e}")
            return '', 500  # Error interno del servidor




    @app.route('/get_reportes_tecnico/<int:tecnico_id>')
    @login_required(role='administrador')
    def get_reportes_tecnico(tecnico_id):
        conn = get_db_connection()
        reportes = conn.execute('''
            SELECT r.id_reporte,c.nombre AS cliente, u.nombre AS ubicacion, r.equipo, r.fecha, 
                r.bloque_mantenimiento_momb, r.cie, r.resumen_actividad, 
                r.refaccion_componente, r.equipo_parado, r.equipo_funcionando,
                r.reparacion, r.mantenimiento, r.falla_averia, r.fallas_24_7, 
                r.emergencia_24_7, r.diagnostico_tecnico, r.traslado_logistica, 
                r.levantamiento_datos_tecnicos, r.modernizacion, r.montaje_nuevo,
                r.micro_inf_final, r.micro_sup_final, r.stop_foso, r.micro_lim_vel,
                r.micro_acunamiento, r.micro_polea_tensora, r.micro_puertas_cab,
                r.micro_puertas_ext, r.stop_techo_cabina
            FROM reportes r
            JOIN clientes c ON r.id_cliente = c.id_cliente
            JOIN ubicaciones u ON r.id_ubicacion = u.id_ubicacion
            WHERE r.id_usuario = ?
        ''', (tecnico_id,)).fetchall()
        conn.close()

        return jsonify([dict(reporte) for reporte in reportes])


    @app.route('/pdc')
    @login_required(role='tecnico')
    def tecnico_panel():
        return render_template('pdc.html')

    # Ruta para levantar un reporte
    @app.route('/levantar_reporte', methods=['GET', 'POST'])
    @login_required(role='tecnico')  # Proteger la ruta solo para técnicos
    def levantar_reporte():
        if request.method == 'POST':
            # Capturar los datos del formulario
            id_cliente = request.form['id_cliente']
            id_ubicacion = request.form['id_ubicacion']
            equipo = request.form['equipo']
            fecha = request.form['fecha']
            bloque_mantenimiento_momb = request.form.get('bloque_mantenimiento')
            cie = request.form['cie']
            resumen = request.form['resumen']
            refaccion = request.form['refaccion']
            equipo_parado = int(request.form['equipo_parado'])
            equipo_funcionando = int(request.form['equipo_funcionando'])

            # Capturar los valores de los combobox de Bloques de Mantenimiento
            bloques = {
                "reparacion": int(request.form['bloque_reparacion']),
                "mantenimiento": int(request.form['mantenimiento']),
                "falla_averia": int(request.form['bloque_falla_averia']),
                "fallas_24_7": int(request.form['bloque_fallas_24_7']),
                "emergencia_24_7": int(request.form['bloque_emergencia_24_7']),
                "diagnostico_tecnico": int(request.form['bloque_diagnostico_tecnico']),
                "traslado_logistica": int(request.form['bloque_traslado_logistica']),
                "levantamiento_datos_tecnicos": int(request.form['bloque_levantamiento_datos_tecnicos']),
                "modernizacion": int(request.form['bloque_modernizacion']),
                "montaje_nuevo": int(request.form['bloque_montaje_nuevo']),
            }

            # Capturar los valores de los combobox de Puntos de Seguridad
            puntos = {
                "micro_inf_final": int(request.form['seguridad_micro_inf_final']),
                "micro_sup_final": int(request.form['seguridad_micro_sup_final']),
                "stop_foso": int(request.form['seguridad_stop_foso']),
                "micro_lim_vel": int(request.form['seguridad_micro_lim_vel']),
                "micro_acunamiento": int(request.form['seguridad_micro_acunamiento']),
                "micro_polea_tensora": int(request.form['seguridad_micro_polea_tensora']),
                "micro_puertas_cab": int(request.form['seguridad_micro_puertas_cab']),
                "micro_puertas_ext": int(request.form['seguridad_micro_puertas_ext']),
                "stop_techo_cabina": int(request.form['seguridad_stop_techo_cabina']),
            }

            # Guardar los datos en la base de datos
            conn = get_db_connection()
            conn.execute('''
                INSERT INTO reportes (
                    id_usuario, id_cliente, id_ubicacion, equipo, fecha, bloque_mantenimiento_momb, cie, resumen_actividad, 
                    refaccion_componente, equipo_parado, equipo_funcionando, reparacion, mantenimiento, falla_averia, 
                    fallas_24_7, emergencia_24_7, diagnostico_tecnico, traslado_logistica, 
                    levantamiento_datos_tecnicos, modernizacion, montaje_nuevo, micro_inf_final, micro_sup_final, 
                    stop_foso, micro_lim_vel, micro_acunamiento, micro_polea_tensora, micro_puertas_cab, 
                    micro_puertas_ext, stop_techo_cabina
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                session.get('user_id'), id_cliente, id_ubicacion, equipo, fecha, bloque_mantenimiento_momb, cie, resumen,
                refaccion, equipo_parado, equipo_funcionando, 
                *bloques.values(), *puntos.values()
            ))
            conn.commit()
            conn.close()

            return redirect('/pdc')  # Redirigir al panel del técnico
        else:
            # Cargar clientes y ubicaciones para las listas desplegables
            conn = get_db_connection()
            clientes = conn.execute('SELECT id_cliente, nombre FROM clientes').fetchall()
            ubicaciones = conn.execute('SELECT id_ubicacion, nombre FROM ubicaciones').fetchall()
            conn.close()
            return render_template('levantar_reporte.html', clientes=clientes, ubicaciones=ubicaciones)

    @app.route('/logout')
    def logout():
        session.clear()  # Limpia la sesión actual
        return redirect('/')  # Redirige al index



    @app.route('/ver_reportes')
    @login_required(role='tecnico')
    def ver_reportes():
        conn = get_db_connection()
        reports = conn.execute('''
            SELECT 
                r.*, 
                c.nombre AS cliente, 
                u.nombre AS ubicacion 
            FROM reportes r
            JOIN clientes c ON r.id_cliente = c.id_cliente
            JOIN ubicaciones u ON r.id_ubicacion = u.id_ubicacion
            WHERE r.id_usuario = ?
        ''', (session['user_id'],)).fetchall()
        conn.close()
        return render_template('ver_reportes.html', reports=[dict(row) for row in reports])

    @app.route('/buscar_reportes')
    @login_required(role='administrador')
    def buscar_reportes():
        filtro = request.args.get('filter')
        valor = request.args.get('value')

        query = '''
            SELECT r.id_reporte, c.nombre AS cliente, u.nombre AS ubicacion, 
                t.nombre_usuario AS tecnico, r.fecha, r.resumen_actividad AS resumen, 
                r.equipo, r.refaccion_componente
            FROM reportes r
            JOIN clientes c ON r.id_cliente = c.id_cliente
            JOIN ubicaciones u ON r.id_ubicacion = u.id_ubicacion
            JOIN usuarios t ON r.id_usuario = t.id_usuario
        '''

        if filtro == 'cliente':
            query += " WHERE c.nombre LIKE ?"
        elif filtro == 'ubicacion':
            query += " WHERE u.nombre LIKE ?"
        elif filtro == 'tecnico':
            query += " WHERE t.nombre_usuario LIKE ?"

        # Ordenar siempre por fecha en orden cronológico
        query += " ORDER BY r.fecha DESC"

        conn = get_db_connection()
        reportes = conn.execute(query, ('%' + valor + '%',)).fetchall()
        conn.close()

        return jsonify([dict(row) for row in reportes])



    @app.route('/descargar_filtrados', methods=['POST'])
    @login_required(role='administrador')
    def descargar_filtrados():
        # Obtener los IDs de los reportes enviados desde el frontend
        ids_reportes = request.json.get('ids_reportes', [])
        print("IDs recibidos:", ids_reportes)  # Verifica los IDs recibidos

        if not ids_reportes:
            return "No hay reportes para descargar", 400

        # Consultar todos los reportes correspondientes a los IDs recibidos
        query = '''
            SELECT r.*, c.nombre AS cliente, u.nombre AS ubicacion, t.nombre_usuario AS tecnico
            FROM reportes r
            JOIN clientes c ON r.id_cliente = c.id_cliente
            JOIN ubicaciones u ON r.id_ubicacion = u.id_ubicacion
            JOIN usuarios t ON r.id_usuario = t.id_usuario
            WHERE r.id_reporte IN ({})
            ORDER BY r.fecha DESC
        '''.format(','.join('?' for _ in ids_reportes))  # Genera una lista de placeholders para evitar SQL injection

        conn = get_db_connection()
        reportes = conn.execute(query, ids_reportes).fetchall()
        conn.close()

        if not reportes:
            return "No se encontraron reportes para los IDs proporcionados", 404

        # Convertir los reportes en diccionarios
        data = [dict(reporte) for reporte in reportes]

        # Generar el PDF
        pdf = generar_pdf_con_formato(data)
        response = make_response(pdf)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = 'attachment; filename=reportes_filtrados.pdf'
        return response

    @app.route('/descargar_seleccion/<int:reporte_id>', methods=['GET'])
    @login_required(role='administrador')
    def descargar_seleccion(reporte_id):
        conn = get_db_connection()
        reporte = conn.execute('''
            SELECT r.*, c.nombre AS cliente, u.nombre AS ubicacion, t.nombre_usuario AS tecnico
            FROM reportes r
            JOIN clientes c ON r.id_cliente = c.id_cliente
            JOIN ubicaciones u ON r.id_ubicacion = u.id_ubicacion
            JOIN usuarios t ON r.id_usuario = t.id_usuario
            WHERE r.id_reporte = ?
        ''', (reporte_id,)).fetchone()
        conn.close()

        if not reporte:
            return "Reporte no encontrado", 404

        pdf = generar_pdf_con_formato([dict(reporte)])
        response = make_response(pdf)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename=reporte_{reporte_id}.pdf'
        return response



    def generar_pdf_con_formato(reportes):
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)

        for reporte in reportes:
            pdf.add_page()
            pdf.set_font("Arial", size=12)

            # Agregar el logo
            pdf.image("static/img/logo.png", x=10, y=10, w=30)  # Ajusta la posición y tamaño si es necesario

            # Espaciado para el logo
            pdf.set_xy(50, 10)  # Mueve el cursor hacia abajo a partir del logo
            pdf.set_font("Arial", style="B", size=14)
            pdf.cell(0, 10, "Reporte de Servicio", ln=True, align="C")
            pdf.ln(20)

            # Datos principales en dos columnas
            pdf.set_font("Arial", size=12)
            pdf.cell(95, 10, f"Cliente: {reporte['cliente']}", border=0)
            pdf.cell(95, 10, f"Ubicación: {reporte['ubicacion']}", border=0, ln=True)
            pdf.cell(95, 10, f"Técnico: {reporte.get('tecnico', 'Sin técnico')}", border=0)  # Técnico
            pdf.cell(95, 10, f"Fecha: {reporte.get('fecha', 'Sin fecha')}", border=0, ln=True)
            pdf.cell(95, 10, f"Equipo: {reporte.get('equipo', 'Sin equipo')}", border=0, ln=True)
            pdf.ln(10)

            # Bloques de mantenimiento y Puntos de seguridad en columnas
            pdf.set_font("Arial", style="B", size=12)
            pdf.cell(0, 10, "Bloque de Mantenimiento (MPMB) y Revisión de Puntos de Seguridad Eléctricos:", ln=True)
            pdf.set_font("Arial", size=12)

            bloques = [
                ("Reparación", "reparacion"),
                ("Emergencia 24/7", "emergencia_24_7"),
                ("Modernización", "modernizacion"),
                ("Mantenimiento", "mantenimiento"),
                ("Diagnóstico Técnico", "diagnostico_tecnico"),
                ("Montaje Nuevo", "montaje_nuevo"),
                ("Falla/Avería", "falla_averia"),
                ("Traslado de Logística", "traslado_logistica"),
                ("Levantamiento de Datos Técnicos", "levantamiento_datos_tecnicos"),
                ("Fallas 24/7", "fallas_24_7")
            ]

            puntos_seguridad = [
                ("Micro Inf. Final", "micro_inf_final"),
                ("Micro Sup. Final", "micro_sup_final"),
                ("Stop de Foso", "stop_foso"),
                ("Micro Lim. de Vel.", "micro_lim_vel"),
                ("Micro Acuñamiento", "micro_acunamiento"),
                ("Micro Polea Tensora", "micro_polea_tensora"),
                ("Micro Puertas Cabina", "micro_puertas_cab"),
                ("Micro Puertas Ext.", "micro_puertas_ext"),
                ("Stop Techo Cabina", "stop_techo_cabina")
            ]

            max_items = max(len(bloques), len(puntos_seguridad))
            for i in range(max_items):
                # Manejo para bloques de mantenimiento
                if i < len(bloques):
                    bloque_label = bloques[i][0]
                    bloque_value = bloques[i][1]
                    bloque_status = f"Sí" if reporte.get(bloque_value, 0) == 1 else "No"
                else:
                    bloque_label = ""
                    bloque_status = ""

                # Manejo para puntos de seguridad
                if i < len(puntos_seguridad):
                    punto_label = puntos_seguridad[i][0]
                    punto_value = puntos_seguridad[i][1]
                    punto_status = f"Sí" if reporte.get(punto_value, 0) == 1 else "No"
                else:
                    punto_label = ""
                    punto_status = ""

                # Agregar las celdas correspondientes
                pdf.cell(95, 10, f"{bloque_label}: {bloque_status}", border=0)
                if punto_label:
                    pdf.cell(95, 10, f"{punto_label}: {punto_status}", border=0, ln=True)
                else:
                    pdf.ln()  # Si no hay punto_label, saltar a la siguiente línea

            pdf.ln(10)





            # Resumen de actividad y refacciones
            pdf.cell(0, 10, "Resumen de Actividad:", ln=True)
            pdf.multi_cell(0, 10, reporte['resumen_actividad'], border=1)
            pdf.ln(5)

            pdf.cell(0, 10, "Refacción y Componente por Sustituir:", ln=True)
            pdf.multi_cell(0, 10, reporte.get('refaccion_componente', ''), border=1)
            pdf.ln(10)

            # Estado del equipo en dos columnas
            pdf.cell(95, 10, f"Equipo parado: {'Sí' if reporte['equipo_parado'] == 1 else 'No'}", border=0)
            pdf.cell(95, 10, f"Equipo funcionando: {'Sí' if reporte['equipo_funcionando'] == 1 else 'No'}", border=0, ln=True)
            pdf.ln(10)


        return pdf.output(dest='S').encode('latin1')




    return app

if __name__ == '__main__':
    app = crear_app()
    app.run()