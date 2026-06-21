document.addEventListener('DOMContentLoaded', () => {
    const socket = io();
    const contenedor = document.getElementById('chatMensajes');
    const form = document.getElementById('formChat');
    const input = document.getElementById('inputMensaje');

    const scrollAbajo = () => {
        contenedor.scrollTop = contenedor.scrollHeight;
    };
    scrollAbajo();

    socket.on('connect', () => {
        // El servidor ya une al usuario a su sala personal usando la sesión (cookie),
        // no hace falta mandar nada extra acá.
    });

    socket.on('nuevo_mensaje', (msg) => {
        const esDeEstaConversacion =
            (msg.remitente_id === MI_ID && msg.destinatario_id === OTRO_ID) ||
            (msg.remitente_id === OTRO_ID && msg.destinatario_id === MI_ID);

        if (!esDeEstaConversacion) return;

        const sinMensajes = contenedor.querySelector('.sin-contactos');
        if (sinMensajes) sinMensajes.remove();

        const div = document.createElement('div');
        div.className = 'mensaje ' + (msg.remitente_id === MI_ID ? 'mensaje-propio' : 'mensaje-otro');

        const p = document.createElement('p');
        p.textContent = msg.contenido;

        const hora = document.createElement('span');
        hora.className = 'mensaje-hora';
        hora.textContent = msg.fecha_hora;

        div.appendChild(p);
        div.appendChild(hora);
        contenedor.appendChild(div);
        scrollAbajo();
    });

    form.addEventListener('submit', (e) => {
        e.preventDefault();
        const contenido = input.value.trim();
        if (!contenido) return;
        socket.emit('enviar_mensaje', { destinatario_id: OTRO_ID, contenido });
        input.value = '';
        input.focus();
    });
});
