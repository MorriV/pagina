function eliminarUsuario(id) {
    if (confirm("¿Estás seguro de eliminar este usuario?")) {
        fetch(`/eliminar_usuario/${id}`, { method: 'DELETE' })
            .then(response => {
                if (response.ok) {
                    alert("Usuario eliminado exitosamente");
                    location.reload();
                } else {
                    alert("Error al eliminar el usuario");
                }
            });
    }
}

function crearUsuario() {
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const role = document.getElementById('role').value;

    if (!username || !password || !role) {
        alert("Por favor, llena todos los campos");
        return;
    }

    fetch('/crear_usuario', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password, role })
    })
    .then(response => {
        if (response.ok) {
            alert("Usuario creado exitosamente");
            location.reload();
        } else {
            alert("Error al crear el usuario");
        }
    });
}
