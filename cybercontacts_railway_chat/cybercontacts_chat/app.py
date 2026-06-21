from flask import Flask, render_template, request, redirect, url_for, session, abort, jsonify
from flask_socketio import SocketIO, join_room, emit
from datetime import date, datetime
import sqlite3
import os
import io
import csv
import re

app = Flask(__name__)
app.secret_key = 'cyber_cotepecos_2026'

socketio = SocketIO(app, async_mode='threading', cors_allowed_origins="*")

# --- SQLite como almacenamiento (seguro para escrituras simultáneas / chat en vivo) ---
DB_FILE = os.path.join(os.path.dirname(__file__), 'cybercontacts.db')


def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON')
    return conn


def init_db():
    conn = get_db()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT UNIQUE NOT NULL,
            contrasena TEXT NOT NULL,
            telefono TEXT UNIQUE NOT NULL
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS contactos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            apellidos TEXT NOT NULL,
            telefono TEXT NOT NULL,
            email TEXT NOT NULL,
            tipo TEXT DEFAULT 'General',
            notas TEXT,
            favorito INTEGER DEFAULT 0,
            usuario_id INTEGER NOT NULL,
            fecha_registro TEXT,
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS mensajes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            remitente_id INTEGER NOT NULL,
            destinatario_id INTEGER NOT NULL,
            contenido TEXT NOT NULL,
            fecha_hora TEXT NOT NULL,
            FOREIGN KEY (remitente_id) REFERENCES usuarios(id) ON DELETE CASCADE,
            FOREIGN KEY (destinatario_id) REFERENCES usuarios(id) ON DELETE CASCADE
        )
    ''')
    conn.commit()
    conn.close()


init_db()


def es_contacto_mutuo(db, usuario_id, otro_id):
    """True si 'otro_id' está agendado como contacto de 'usuario_id' (coincidencia por teléfono)."""
    otro = db.execute('SELECT telefono FROM usuarios WHERE id = ?', (otro_id,)).fetchone()
    if not otro:
        return False
    fila = db.execute(
        'SELECT id FROM contactos WHERE usuario_id = ? AND telefono = ?',
        (usuario_id, otro['telefono'])
    ).fetchone()
    return fila is not None


# --- Ruta: registro ---
@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        usuario = request.form.get('usuario', '').strip()
        contrasena = request.form.get('contrasena', '').strip()
        telefono = request.form.get('telefono', '').strip()

        if not usuario or not contrasena or not telefono:
            return render_template('registro.html', error='Completá usuario, contraseña y teléfono')

        if not re.fullmatch(r'[0-9\-]{8,12}', telefono):
            return render_template('registro.html', error='Ingresá un teléfono válido (solo números, 8 a 12 dígitos)')

        db = get_db()
        if db.execute('SELECT id FROM usuarios WHERE usuario = ?', (usuario,)).fetchone():
            db.close()
            return render_template('registro.html', error='Ese usuario ya existe')
        if db.execute('SELECT id FROM usuarios WHERE telefono = ?', (telefono,)).fetchone():
            db.close()
            return render_template('registro.html', error='Ese número de teléfono ya está registrado por otra cuenta')

        db.execute('INSERT INTO usuarios (usuario, contrasena, telefono) VALUES (?, ?, ?)',
                   (usuario, contrasena, telefono))
        db.commit()
        db.close()

        return redirect(url_for('login'))

    return render_template('registro.html')


# --- Ruta: inicio (protegida) ---
@app.route('/')
def inicio():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))

    db = get_db()
    filas = db.execute(
        'SELECT * FROM contactos WHERE usuario_id = ? ORDER BY nombre COLLATE NOCASE',
        (session['usuario_id'],)
    ).fetchall()

    contactos = []
    for c in filas:
        match = db.execute(
            'SELECT id, usuario FROM usuarios WHERE telefono = ? AND id != ?',
            (c['telefono'], session['usuario_id'])
        ).fetchone()
        item = dict(c)
        item['chat_usuario_id'] = match['id'] if match else None
        item['chat_usuario_nombre'] = match['usuario'] if match else None
        contactos.append(item)
    db.close()

    return render_template('index.html', usuarios=session['usuario'], mi_id=session['usuario_id'], contactos=contactos)


# --- Ruta: login ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'usuario_id' in session:
        return redirect(url_for('inicio'))

    if request.method == 'POST':
        usuario = request.form.get('usuario', '')
        contrasena = request.form.get('contrasena', '')

        db = get_db()
        fila = db.execute(
            'SELECT id, usuario FROM usuarios WHERE usuario = ? AND contrasena = ?',
            (usuario, contrasena)
        ).fetchone()
        db.close()

        if fila:
            session['usuario'] = fila['usuario']
            session['usuario_id'] = fila['id']
            return redirect(url_for('inicio'))
        else:
            return render_template('login.html', error='Usuario o contraseña incorrectos')

    return render_template('login.html')


# --- Ruta: agregar contacto ---
@app.route('/contacto/nuevo', methods=['POST'])
def nuevo_contacto():
    if 'usuario_id' not in session:
        return jsonify(ok=False, error="Tu sesión expiró, volvé a iniciar sesión"), 401

    nombre = request.form.get('nombre', '').strip()
    apellidos = request.form.get('apellidos', '').strip()
    email = request.form.get('email', '').strip()
    telefono = request.form.get('telefono', '').strip()
    tipo = request.form.get('tipo', 'General').strip()
    notas = request.form.get('notas', '').strip()
    favorito = 1 if request.form.get('favorito') == 'on' else 0

    if not nombre or not apellidos or not email or not telefono:
        return jsonify(ok=False, error="Completá nombre, apellidos, correo y teléfono"), 200

    db = get_db()

    # Evita agregar un contacto que ya existe (mismo teléfono) en tu propia agenda.
    existente = db.execute(
        'SELECT nombre, apellidos FROM contactos WHERE usuario_id = ? AND telefono = ?',
        (session['usuario_id'], telefono)
    ).fetchone()
    if existente:
        db.close()
        return jsonify(ok=False, error=f"Ya tenés un contacto con el teléfono {telefono} ({existente['nombre']} {existente['apellidos']})"), 200

    db.execute('''
        INSERT INTO contactos (nombre, apellidos, telefono, email, tipo, notas, favorito, usuario_id, fecha_registro)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (nombre, apellidos, telefono, email, tipo, notas, favorito, session['usuario_id'], date.today().isoformat()))
    db.commit()
    db.close()

    return jsonify(ok=True)


# --- Ruta: editar contacto ---
@app.route('/contacto/<int:contacto_id>/editar', methods=['POST'])
def editar_contacto(contacto_id):
    if 'usuario_id' not in session:
        return jsonify(ok=False, error="Tu sesión expiró, volvé a iniciar sesión"), 401

    db = get_db()
    fila = db.execute('SELECT id FROM contactos WHERE id = ? AND usuario_id = ?',
                       (contacto_id, session['usuario_id'])).fetchone()
    if not fila:
        db.close()
        abort(404)

    nombre = request.form.get('nombre', '').strip()
    apellidos = request.form.get('apellidos', '').strip()
    email = request.form.get('email', '').strip()
    telefono = request.form.get('telefono', '').strip()
    tipo = request.form.get('tipo', 'General').strip()
    notas = request.form.get('notas', '').strip()
    favorito = 1 if request.form.get('favorito') == 'on' else 0

    if not nombre or not apellidos or not email or not telefono:
        db.close()
        return jsonify(ok=False, error="Completá nombre, apellidos, correo y teléfono"), 200

    # Evita que el teléfono editado choque con el de OTRO contacto tuyo.
    otro = db.execute(
        'SELECT nombre, apellidos FROM contactos WHERE usuario_id = ? AND telefono = ? AND id != ?',
        (session['usuario_id'], telefono, contacto_id)
    ).fetchone()
    if otro:
        db.close()
        return jsonify(ok=False, error=f"Ya tenés otro contacto con el teléfono {telefono} ({otro['nombre']} {otro['apellidos']})"), 200

    db.execute('''
        UPDATE contactos SET nombre=?, apellidos=?, telefono=?, email=?, tipo=?, notas=?, favorito=?
        WHERE id = ? AND usuario_id = ?
    ''', (nombre, apellidos, telefono, email, tipo, notas, favorito, contacto_id, session['usuario_id']))
    db.commit()
    db.close()

    return jsonify(ok=True)


# --- Ruta: eliminar contacto ---
@app.route('/contacto/<int:contacto_id>/eliminar', methods=['POST'])
def eliminar_contacto(contacto_id):
    if 'usuario_id' not in session:
        return redirect(url_for('login'))

    db = get_db()
    fila = db.execute('SELECT id FROM contactos WHERE id = ? AND usuario_id = ?',
                       (contacto_id, session['usuario_id'])).fetchone()
    if not fila:
        db.close()
        abort(404)

    # Borra SOLO esta fila, dueña de este usuario_id -> nunca afecta a otros usuarios.
    db.execute('DELETE FROM contactos WHERE id = ? AND usuario_id = ?', (contacto_id, session['usuario_id']))
    db.commit()
    db.close()

    return redirect(url_for('inicio'))


# --- Ruta: dashboard / reporte general ---
@app.route('/reporte')
def reporte():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))

    db = get_db()
    contactos = db.execute('SELECT * FROM contactos WHERE usuario_id = ?', (session['usuario_id'],)).fetchall()
    db.close()

    total = len(contactos)
    favoritos = [c for c in contactos if c['tipo'] == 'Favorito' or c['favorito']]
    cantidad_favoritos = len(favoritos)
    cantidad_generales = total - cantidad_favoritos

    hoy = date.today().isoformat()
    nuevos_hoy = len([c for c in contactos if c['fecha_registro'] == hoy])

    favoritos = sorted(favoritos, key=lambda c: (c['nombre'] or '').lower())

    pct_favoritos = round((cantidad_favoritos / total) * 100, 1) if total else 0
    pct_generales = round((cantidad_generales / total) * 100, 1) if total else 0

    ahora = datetime.now()

    return render_template(
        'reporte.html',
        mi_id=session['usuario_id'],
        total=total,
        favoritos=favoritos,
        cantidad_favoritos=cantidad_favoritos,
        cantidad_generales=cantidad_generales,
        nuevos_hoy=nuevos_hoy,
        pct_favoritos=pct_favoritos,
        pct_generales=pct_generales,
        fecha_generado=ahora.strftime('%d/%m/%Y'),
        hora_generado=ahora.strftime('%I:%M %p'),
    )


# --- Ruta: exportar reporte a CSV ---
@app.route('/reporte/exportar')
def exportar_reporte():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))

    db = get_db()
    contactos = db.execute('SELECT * FROM contactos WHERE usuario_id = ?', (session['usuario_id'],)).fetchall()
    db.close()

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(['Nombre', 'Apellidos', 'Telefono', 'Email', 'Tipo', 'Notas'])
    for c in contactos:
        writer.writerow([c['nombre'], c['apellidos'], c['telefono'], c['email'], c['tipo'], c['notas']])

    from flask import Response
    return Response(
        buffer.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment;filename=reporte_cybercontacts.csv'}
    )


# --- Ruta: chat 1 a 1 con un contacto que también tenga cuenta ---
@app.route('/chat/<int:otro_id>')
def chat(otro_id):
    if 'usuario_id' not in session:
        return redirect(url_for('login'))

    db = get_db()
    otro = db.execute('SELECT id, usuario, telefono FROM usuarios WHERE id = ?', (otro_id,)).fetchone()
    if not otro:
        db.close()
        abort(404)

    # Solo se puede chatear si esa persona está agendada como contacto tuyo (por teléfono).
    if not es_contacto_mutuo(db, session['usuario_id'], otro_id):
        db.close()
        abort(403)

    mensajes = db.execute('''
        SELECT * FROM mensajes
        WHERE (remitente_id = ? AND destinatario_id = ?)
           OR (remitente_id = ? AND destinatario_id = ?)
        ORDER BY id ASC
    ''', (session['usuario_id'], otro_id, otro_id, session['usuario_id'])).fetchall()
    db.close()

    return render_template('chat.html', otro=otro, mensajes=mensajes, mi_id=session['usuario_id'])


# --- Eventos en tiempo real (Socket.IO) ---
@socketio.on('connect')
def socket_connect():
    if 'usuario_id' in session:
        join_room(f"user_{session['usuario_id']}")


@socketio.on('enviar_mensaje')
def socket_enviar_mensaje(data):
    if 'usuario_id' not in session:
        return

    destinatario_id = data.get('destinatario_id')
    contenido = (data.get('contenido') or '').strip()
    if not contenido or not destinatario_id:
        return

    db = get_db()
    if not es_contacto_mutuo(db, session['usuario_id'], destinatario_id):
        db.close()
        return

    ahora = datetime.now().strftime('%d/%m/%Y %H:%M')
    cur = db.execute(
        'INSERT INTO mensajes (remitente_id, destinatario_id, contenido, fecha_hora) VALUES (?, ?, ?, ?)',
        (session['usuario_id'], destinatario_id, contenido, ahora)
    )
    db.commit()
    mensaje_id = cur.lastrowid
    db.close()

    payload = {
        'id': mensaje_id,
        'remitente_id': session['usuario_id'],
        'remitente_nombre': session['usuario'],
        'destinatario_id': destinatario_id,
        'contenido': contenido,
        'fecha_hora': ahora,
    }
    emit('nuevo_mensaje', payload, room=f"user_{destinatario_id}")
    emit('nuevo_mensaje', payload, room=f"user_{session['usuario_id']}")


# --- Ruta: logout ---
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


# --- Arrancar servidor ---
if __name__ == '__main__':
    puerto = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=puerto, debug=False, allow_unsafe_werkzeug=True)
