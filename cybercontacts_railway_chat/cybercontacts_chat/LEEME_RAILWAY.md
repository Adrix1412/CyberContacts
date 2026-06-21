# CyberContacts — versión Railway (SQLite + Chat en tiempo real)

## Subir a Railway
1. Subí esta carpeta a un repo de GitHub (o conectá Railway directo a la carpeta).
2. En Railway: "New Project" → "Deploy from GitHub repo" → elegí el repo.
3. Railway detecta `requirements.txt` y `Procfile` automáticamente, no hace falta configurar nada más.
4. Railway asigna el puerto por variable de entorno `PORT` — el código ya lo lee solo (`app.py`, última línea).
5. Cuando termine el deploy, te da una URL pública tipo `https://tuapp.up.railway.app` — esa es la que compartís.

## Importante sobre la base de datos
- `cybercontacts.db` se crea solo la primera vez que corre el server (no subas un archivo `.db` viejo con datos de prueba).
- En el plan gratuito de Railway el disco puede reiniciarse si el contenedor se redeploya — si eso pasa, se borran los datos. Si necesitás que persistan entre deploys, en Railway agregá un "Volume" y montalo en la carpeta del proyecto.

## Correr en tu compu para probar antes de subir
```
pip install -r requirements.txt
python app.py
```
Abrí `http://127.0.0.1:5000`

## Cómo funciona el chat
- Cada cuenta tiene un número de teléfono único.
- El botón "💬 Chat" aparece en un contacto SOLO si el teléfono de ese contacto coincide con el teléfono de otra cuenta registrada en el sistema.
- Los mensajes son en tiempo real (WebSocket vía Socket.IO) y quedan guardados en `cybercontacts.db`.
