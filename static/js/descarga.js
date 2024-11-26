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
                        <td>${reporte.tecnico}</td>
                        <td>${reporte.fecha}</td>
                        <td>${reporte.resumen}</td>
                    </tr>
                `;
                tableBody.innerHTML += row;
            });
        })
        .catch(error => console.error('Error al buscar reportes:', error));
}

function descargarFiltrados() {
    const tabla = document.getElementById('reportTable');
    const filas = tabla.querySelectorAll('tr');
    const reportes = Array.from(filas).map(fila => {
        const columnas = fila.querySelectorAll('td');
        return {
            cliente: columnas[0].textContent.trim(),
            ubicacion: columnas[1].textContent.trim(),
            tecnico: columnas[2].textContent.trim(),
            fecha: columnas[3].textContent.trim(),
            resumen_actividad: columnas[4].textContent.trim(),
            equipo: columnas[5]?.textContent.trim() || "", // Incluye equipo si está presente
            equipo_parado: columnas[6]?.textContent.trim() || "No", // Valor por defecto si no está
            equipo_funcionando: columnas[7]?.textContent.trim() || "No" // Valor por defecto si no está
        };
    });

    fetch('/descargar_filtrados', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ reportes }) // Enviar los datos correctamente al servidor
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
