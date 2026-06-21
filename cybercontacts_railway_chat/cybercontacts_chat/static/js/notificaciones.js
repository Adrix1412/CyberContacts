// Se incluye en index.html, reporte.html y chat.html.
// Requiere que la página declare antes: const MI_ID = <id del usuario logueado>;
// En chat.html además se declara CHAT_CON_ID para no duplicar el aviso del mensaje
// que ya se está mostrando dentro de esa misma conversación.

document.addEventListener('DOMContentLoaded', () => {
    if (typeof MI_ID === 'undefined') return;

    const socket = io();

    const yaEstoyViendoEseChat = (remitenteId) => {
        return typeof CHAT_CON_ID !== 'undefined' && CHAT_CON_ID === remitenteId;
    };

    const crearContenedor = () => {
        let cont = document.getElementById('notifContenedor');
        if (!cont) {
            cont = document.createElement('div');
            cont.id = 'notifContenedor';
            cont.className = 'notif-contenedor';
            document.body.appendChild(cont);
        }
        return cont;
    };

    const mostrarNotificacion = (msg) => {
        const cont = crearContenedor();

        const toast = document.createElement('div');
        toast.className = 'toast-notificacion';
        toast.innerHTML = `
            <span class="toast-icono">💬</span>
            <div class="toast-texto">
                <strong></strong>
                <p></p>
            </div>
        `;
        toast.querySelector('strong').textContent = msg.remitente_nombre || 'Nuevo mensaje';
        toast.querySelector('p').textContent = msg.contenido;

        toast.addEventListener('click', () => {
            window.location.href = `/chat/${msg.remitente_id}`;
        });

        cont.appendChild(toast);

        // Forzar el reflow para que la animación de entrada se vea
        requestAnimationFrame(() => toast.classList.add('toast-visible'));

        setTimeout(() => {
            toast.classList.remove('toast-visible');
            toast.classList.add('toast-saliendo');
            setTimeout(() => toast.remove(), 300);
        }, 5000);
    };

    socket.on('nuevo_mensaje', (msg) => {
        if (msg.destinatario_id !== MI_ID) return;        // no es para mí
        if (msg.remitente_id === MI_ID) return;            // es un mensaje que yo mismo mandé (eco a mi propia sala)
        if (yaEstoyViendoEseChat(msg.remitente_id)) return; // ya lo estoy viendo en pantalla

        mostrarNotificacion(msg);
    });
});
