document.addEventListener('DOMContentLoaded', () => {
    const modalAgregar = document.getElementById('modalAgregar');
    const modalEditar = document.getElementById('modalEditar');
    const modalEliminar = document.getElementById('modalEliminar');
    const todosLosModales = [modalAgregar, modalEditar, modalEliminar];

    const abrir = (modal) => modal.classList.add('activo');
    const cerrar = (modal) => {
        modal.classList.remove('activo');
        modal.querySelectorAll('.error-modal').forEach((el) => {
            el.style.display = 'none';
            el.textContent = '';
        });
    };
    const cerrarTodos = () => todosLosModales.forEach(cerrar);

    // Botón "+ Agregar"
    document.getElementById('btnAgregar').addEventListener('click', () => {
        document.getElementById('formAgregar').reset();
        abrir(modalAgregar);
    });

    // Botones de cancelar / cerrar dentro de cada modal
    document.querySelectorAll('.btn-cerrar-modal').forEach((btn) => {
        btn.addEventListener('click', () => {
            btn.closest('.modal-overlay').classList.remove('activo');
        });
    });

    // Cerrar al hacer click en el fondo oscuro
    todosLosModales.forEach((modal) => {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) cerrar(modal);
        });
    });

    // Cerrar con la tecla Escape
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') cerrarTodos();
    });

    // Sincroniza el select "Tipo de contacto" con el switch "Favorito"
    const sincronizar = (select, checkbox) => {
        if (!select || !checkbox) return;
        select.addEventListener('change', () => {
            checkbox.checked = select.value === 'Favorito';
        });
        checkbox.addEventListener('change', () => {
            select.value = checkbox.checked ? 'Favorito' : 'General';
        });
    };
    sincronizar(document.querySelector('#modalAgregar .select-tipo'), document.querySelector('#modalAgregar .check-favorito'));
    sincronizar(document.getElementById('editTipo'), document.getElementById('editFavorito'));

    // Envía un form de contacto por fetch y muestra el error en el propio modal (sin recargar ni perder lo escrito)
    const enviarFormContacto = (form, elementoError) => {
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            elementoError.style.display = 'none';
            elementoError.textContent = '';

            const boton = form.querySelector('button[type="submit"]');
            const textoOriginal = boton.textContent;
            boton.disabled = true;
            boton.textContent = 'Guardando...';

            try {
                const resp = await fetch(form.action, { method: 'POST', body: new FormData(form) });
                const data = await resp.json();

                if (data.ok) {
                    window.location.reload();
                } else {
                    elementoError.textContent = data.error || 'No se pudo guardar el contacto';
                    elementoError.style.display = 'block';
                }
            } catch (err) {
                elementoError.textContent = 'No se pudo conectar con el servidor';
                elementoError.style.display = 'block';
            } finally {
                boton.disabled = false;
                boton.textContent = textoOriginal;
            }
        });
    };

    enviarFormContacto(document.getElementById('formAgregar'), document.getElementById('errorAgregar'));
    enviarFormContacto(document.getElementById('formEditar'), document.getElementById('errorEditar'));

    // Botón "Editar" de cada fila -> precarga el modal de edición
    document.querySelectorAll('.btn-accion.editar').forEach((btn) => {
        btn.addEventListener('click', () => {
            const fila = btn.closest('tr');
            const id = fila.dataset.id;

            document.getElementById('formEditar').action = `/contacto/${id}/editar`;
            document.getElementById('editNombre').value = fila.dataset.nombre;
            document.getElementById('editApellidos').value = fila.dataset.apellidos;
            document.getElementById('editEmail').value = fila.dataset.email;
            document.getElementById('editTelefono').value = fila.dataset.telefono;
            document.getElementById('editTipo').value = fila.dataset.tipo;
            document.getElementById('editNotas').value = fila.dataset.notas;
            document.getElementById('editFavorito').checked = fila.dataset.favorito === 'True';
            document.getElementById('editarSubtitulo').textContent =
                `${fila.dataset.nombre} ${fila.dataset.apellidos} · ID #${String(id).padStart(4, '0')}`;

            abrir(modalEditar);
        });
    });

    // Botón "Eliminar" de cada fila -> precarga el modal de confirmación
    document.querySelectorAll('.btn-accion.eliminar').forEach((btn) => {
        btn.addEventListener('click', () => {
            const fila = btn.closest('tr');
            const id = fila.dataset.id;

            document.getElementById('formEliminar').action = `/contacto/${id}/eliminar`;
            document.getElementById('delNombre').textContent = `${fila.dataset.nombre} ${fila.dataset.apellidos}`;
            document.getElementById('delDetalle').textContent = `${fila.dataset.telefono} · ${fila.dataset.email}`;

            abrir(modalEliminar);
        });
    });

    // Buscador en vivo (filtra por nombre, apellidos, teléfono o correo)
    const buscador = document.getElementById('buscador');
    const btnBuscar = document.getElementById('btnBuscar');

    const filtrar = () => {
        const q = buscador.value.trim().toLowerCase();
        document.querySelectorAll('#tablaContactos tbody tr.fila-contacto').forEach((fila) => {
            const texto = `${fila.dataset.nombre} ${fila.dataset.apellidos} ${fila.dataset.telefono} ${fila.dataset.email}`.toLowerCase();
            fila.style.display = texto.includes(q) ? '' : 'none';
        });
    };

    if (buscador) {
        buscador.addEventListener('input', filtrar);
        buscador.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') filtrar();
        });
    }
    if (btnBuscar) {
        btnBuscar.addEventListener('click', filtrar);
    }
});
