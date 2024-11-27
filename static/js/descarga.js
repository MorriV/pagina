function buscarReportes() {
    const filter = document.getElementById('filter').value;
    const filterValue = document.getElementById('filterValue').value;

    fetch(`/buscar_reportes?filter=${filter}&value=${filterValue}`)
        .then(response => response.json())
        .then(data => {
            const tableBody = document.getElementById('reportTable');
            tableBody.innerHTML = ''; // Limpiar la tabla

            data.forEach(reporte => {
                const row = `
                    <tr onclick="selectRow(this)" data-id="${reporte.id_reporte}">
                        <td>${reporte.cliente}</td>
                        <td>${reporte.ubicacion}</td>
                        <td>${reporte.tecnico || "Sin técnico"}</td> <!-- Agregar técnico -->
                        <td>${reporte.fecha || "Sin fecha"}</td>
                        <td>${reporte.resumen || "Sin resumen"}</td>
                        <td>${reporte.equipo || "Sin equipo"}</td>
                        <td>${reporte.refaccion_componente || "Sin refacción"}</td>
                    </tr>
                `;
                tableBody.innerHTML += row;
            });
        })
        .catch(error => console.error('Error al buscar reportes:', error));
}



function descargarFiltrados() {
    // Obtén los IDs de los reportes visibles en la tabla
    const tabla = document.getElementById('reportTable');
    const filas = tabla.querySelectorAll('tr');
    const idsReportes = Array.from(filas).map(fila => fila.getAttribute('data-id'));

    if (idsReportes.length === 0) {
        alert("No hay reportes para descargar.");
        return;
    }

    // Enviar los IDs al servidor
    fetch('/descargar_filtrados', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ids_reportes: idsReportes })
    })
    .then(response => {
        if (response.ok) {
            return response.blob();
        }
        throw new Error("Error al generar el PDF");
    })
    .then(blob => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = "reportes_filtrados.pdf";
        document.body.appendChild(a);
        a.click();
        a.remove();
    })
    .catch(error => {
        alert("Error al descargar los reportes: " + error.message);
    });
}






function descargarSeleccion() {
    const selectedRow = document.querySelector('tr.selected'); // Buscar la fila seleccionada
    if (!selectedRow) {
        alert('Por favor, seleccione un reporte para descargar.');
        return;
    }

    const reportId = selectedRow.getAttribute('data-id'); // Obtener el ID del reporte seleccionado
    window.location.href = `/descargar_seleccion/${reportId}`; // Redirigir a la ruta de descarga
}

function selectRow(row) {
    // Remover la clase "selected" de cualquier fila previamente seleccionada
    document.querySelectorAll('tr').forEach(r => r.classList.remove('selected'));

    // Agregar la clase "selected" a la fila actual
    row.classList.add('selected');
}
