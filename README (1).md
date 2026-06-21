# 🔮 CyberContacts

Sistema de gestión de contactos con **chat en tiempo real**, desarrollado para el curso de Programación Web — COTEPECOS 2026.

Agenda tus contactos y, si alguno de ellos también tiene cuenta en el sistema (mismo número de teléfono), chateá con esa persona en vivo.

---

## ⚡ Características

- 🔐 **Cuentas de usuario** con usuario, contraseña y teléfono (único por cuenta).
- 📇 **Agenda de contactos**: agregar, editar y eliminar desde ventanas emergentes, sin recargar la página.
- 🚫 **Validación de duplicados**: no se puede repetir un mismo número de teléfono ni entre cuentas ni entre contactos propios.
- ⭐ **Contactos favoritos** con badge visual y switch sincronizado con el tipo de contacto.
- 🔍 **Buscador en vivo** por nombre, apellidos, teléfono o correo.
- 📊 **Dashboard / Reporte general**: totales, favoritos vs. generales, contactos nuevos del día y exportación a CSV.
- 💬 **Chat en tiempo real (WebSocket)**: si un contacto tuyo también tiene cuenta (coincide el teléfono), te aparece un botón para chatear en vivo con esa persona.
- 🔒 **Seguridad por dueño**: cada usuario solo ve, edita, borra y chatea con SUS propios datos. Probado contra accesos cruzados entre cuentas.

---

## 🛠️ Stack técnico

| Capa            | Tecnología                          |
|-----------------|--------------------------------------|
| Backend         | Python 3 + Flask                     |
| Tiempo real     | Flask-SocketIO (Socket.IO)           |
| Base de datos   | SQLite (`sqlite3`, sin ORM)          |
| Frontend        | HTML + CSS + JavaScript puro (vanilla)|
| Estilo          | Cyberpunk, fuente Rajdhani (Google Fonts) |

> Esta es la versión pensada para desplegar en **Railway**, por eso usa SQLite en vez de Excel: aguanta escrituras simultáneas (varios usuarios chateando a la vez) sin riesgo de corromper datos.

---

## 📁 Estructura del proyecto

```
cybercontacts_chat/
├── app.py                  # Backend: rutas, lógica y eventos de Socket.IO
├── requirements.txt        # Dependencias de Python
├── Procfile                # Comando de arranque para Railway
├── cybercontacts.db        # Base de datos SQLite (se crea sola, no se sube al repo)
├── static/
│   ├── css/style.css       # Estilos (tema cyberpunk)
│   └── js/
│       ├── app.js          # Modales, buscador, validaciones de formularios
│       └── chat.js         # Cliente de Socket.IO para el chat
└── templates/
    ├── login.html
    ├── registro.html
    ├── index.html           # Agenda + modales de agregar/editar/eliminar
    ├── chat.html            # Ventana de chat en tiempo real
    └── reporte.html         # Dashboard / reporte general
```

---

## 💻 Correr en local

Necesitás Python 3.10 o superior.

```bash
# 1. Cloná el repo
git clone https://github.com/Adrix1412/cybercontacts.git
cd cybercontacts

# 2. (Opcional pero recomendado) creá un entorno virtual
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac / Linux

# 3. Instalá las dependencias
pip install -r requirements.txt

# 4. Corré el servidor
python app.py
```

Abrí **http://127.0.0.1:5000** en el navegador. La base de datos (`cybercontacts.db`) se crea automáticamente la primera vez que corre.

---

## 🚀 Desplegar en Railway

1. Subí este proyecto a un repositorio de GitHub (los pasos están más abajo).
2. Entrá a [railway.app](https://railway.app) → **New Project** → **Deploy from GitHub repo**.
3. Elegí el repositorio. Railway detecta `requirements.txt` y `Procfile` automáticamente — no hace falta configurar nada más.
4. Esperá a que termine el build. Railway te da una URL pública tipo `https://tuapp.up.railway.app`.

### ⚠️ Importante sobre la persistencia de datos

En el plan gratuito de Railway, el sistema de archivos puede reiniciarse cuando se hace un nuevo deploy, y eso borraría `cybercontacts.db`. Si querés que los contactos, usuarios y mensajes sobrevivan entre actualizaciones, agregá un **Volume** en Railway y montalo en la carpeta del proyecto antes de invitar gente a usarlo en serio.

---

## 📤 Subir este proyecto a GitHub (primera vez)

```bash
cd cybercontacts_chat
git init
git add .
git commit -m "CyberContacts: chat en tiempo real"
git branch -M main
git remote add origin https://github.com/Adrix1412/cybercontacts.git
git push -u origin main
```

Si el repo en GitHub ya existe con contenido (por ejemplo un README inicial), primero hacé `git pull origin main --allow-unrelated-histories` antes del `push`.

> El archivo `.gitignore` incluido ya excluye `cybercontacts.db`, `__pycache__/` y entornos virtuales, así que no se sube basura ni datos de usuarios reales al repositorio.

---

## 💬 Cómo funciona el chat

1. Cada cuenta se registra con un número de teléfono único.
2. Cuando agregás un contacto, el sistema revisa si ese teléfono coincide con el de otra cuenta registrada.
3. Si coincide, aparece el botón **💬 Chat** en esa fila de tu agenda.
4. Al entrar, se abre una conversación 1 a 1 en tiempo real (WebSocket) con esa persona. Los mensajes quedan guardados en la base de datos.
5. Nadie puede abrir ni mandar mensajes a un chat si esa persona no está agendada como su contacto — se valida tanto al abrir la ventana de chat como al enviar cada mensaje.

---

## 👤 Autor

**Adrián Josué Durán Jiménez (Adrix)**
11° año, Desarrollo Web — COTEPECOS, Ciudad Colón, Costa Rica
GitHub: [@Adrix1412](https://github.com/Adrix1412)
