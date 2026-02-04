import re

# Read the file
with open(r'c:\Users\jrg23\OneDrive\Documentos\Antigravity\Reparaciones\index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update form submit to include priority
old_submit = '''        document.getElementById('reporteForm').addEventListener('submit', function (e) {
            e.preventDefault();
            const unidad = document.getElementById('selectorUnidad').value;
            const obs = document.getElementById('observaciones').value.trim();
            const checkboxes = document.querySelectorAll('input[name="fallas"]:checked');
            if (!unidad || checkboxes.length === 0) { mostrarToast('⚠️ Faltan datos', 'danger'); return; }
            let listaFallas = Array.from(checkboxes).map(cb => cb.value);
            push(dbRef, {
                unidad: unidad, fallas: listaFallas, observaciones: obs,
                fecha: new Date().toLocaleDateString('es-AR'), hora: new Date().toLocaleTimeString('es-AR', { hour: '2-digit', minute: '2-digit' }),
                estado: "Pendiente", usuario: rolActual
            }).then(() => {
                mostrarToast('✅ Reporte enviado.', 'success'); document.getElementById('reporteForm').reset();
                document.getElementById('panelFallas').style.display = 'none'; document.getElementById('selectorUnidad').disabled = true;
                document.getElementById('selectorUnidad').innerHTML = '<option value="">-- Primero elija grupo --</option>';
            });
        });'''

new_submit = '''        // --- VALIDACIONES EN TIEMPO REAL ---
        const camposRequeridos = ['selectorGrupo', 'selector Unidad', 'selectorPrioridad'];
        
        document.getElementById('selectorPrioridad').addEventListener('change', function() {
            if(this.value) {
                this.classList.remove('is-invalid');
                this.classList.add('is-valid');
            } else {
                this.classList.remove('is-valid');
                this.classList.add('is-invalid');
            }
        });

        document.getElementById('reporteForm').addEventListener('submit', function (e) {
            e.preventDefault();
            const unidad = document.getElementById('selectorUnidad').value;
            const prioridad = document.getElementById('selectorPrioridad').value;
            const obs = document.getElementById('observaciones').value.trim();
            const checkboxes = document.querySelectorAll('input[name="fallas"]:checked');
            
            // Validaciones
            if (!unidad || checkboxes.length === 0 || !prioridad) { 
                mostrarToast('⚠️ Faltan datos obligatorios', 'danger');
                if(!prioridad) document.getElementById('selectorPrioridad').classList.add('is-invalid');
                return; 
            }
            
            let listaFallas = Array.from(checkboxes).map(cb => cb.value);
            push(dbRef, {
                unidad: unidad, 
                fallas: listaFallas, 
                observaciones: obs,
                prioridad: prioridad,
                fecha: new Date().toLocaleDateString('es-AR'), 
                hora: new Date().toLocaleTimeString('es-AR', { hour: '2-digit', minute: '2-digit' }),
                estado: "Pendiente", 
                usuario: rolActual
            }).then(() => {
                mostrarToast('✅ Reporte enviado.', 'success'); 
                document.getElementById('reporteForm').reset();
                document.getElementById('panelFallas').style.display = 'none'; 
                document.getElementById('selectorUnidad').disabled = true;
                document.getElementById('selectorUnidad').innerHTML = '<option value="">-- Primero elija grupo --</option>';
                document.getElementById('selectorPrioridad').classList.remove('is-valid');
            });
        });'''

content = content.replace(old_submit, new_submit)

# 2. Add filter functions before "UI Helpers"
filter_functions = '''        
        // --- FILTROS AVANZADOS ---
        window.toggleFiltros = function() {
            const panel = document.getElementById('panelFiltros');
            panel.style.display = panel.style.display === 'none' ? 'block' : 'none';
        };
        
        window.aplicarFiltros = function() {
            const filtroEstado = document.getElementById('filtroEstado').value;
            const filtroPrioridad = document.getElementById('filtroPrioridad').value;
            const filas = document.querySelectorAll('#tablaCuerpo tr');
            let contador = 0;
            
            filas.forEach(fila => {
                const estado = fila.querySelector('td:nth-child(4)')?.textContent.includes('Listo') ? 'Completado' : 'Pendiente';
                const prioridad = fila.dataset.prioridad || '';
                
                let mostrar = true;
                
                if(filtroEstado && estado !== filtroEstado) mostrar = false;
                if(filtroPrioridad && prioridad !== filtroPrioridad) mostrar = false;
                
                fila.style.display = mostrar ? '' : 'none';
                if(mostrar) contador++;
            });
            
            document.getElementById('contadorResultados').textContent = 
                contador === filas.length ? 'Mostrando todos los reportes' : 
                `Mostrando ${contador} de ${filas.length} reportes`;
        };
        
        window.limpiarFiltros = function() {
            document.getElementById('filtroEstado').value = '';
            document.getElementById('filtroPrioridad').value = '';
            document.getElementById('busquedaTabla').value = '';
            document.querySelectorAll('#tablaCuerpo tr').forEach(row => row.style.display = '');
            document.getElementById('contadorResultados').textContent = 'Mostrando todos los reportes';
        };
        
        // UI Helpers'''

content = content.replace('        // UI Helpers', filter_functions)

# 3. Update crearFila function to include priority
old_crear_fila = '''    function crearFila(key, data) {
        let badges = (data.fallas || []).map(f => `<span class="badge rounded-pill ${f === 'GPS' ? 'bg-danger' : f === 'RFID' ? 'bg-warning text-dark' : f === 'NVR' ? 'bg-info text-dark' : 'bg-success'} badge-falla border border-light shadow-sm">${f}</span>`).join('');
        let acciones = `<button onclick="mostrarObservaciones('${(data.observaciones || '').replace(/'/g, "\\\\'")}')\" class="btn btn-sm btn-outline-info me-1 border-0"><i class="fas fa-eye"></i></button>`;

        if (rolActual === 'Técnico' || rolActual === 'Supervisor') {
            if (data.estado !== "Completado") acciones += `<button onclick="marcarCompletado('${key}')\" class="btn btn-sm btn-outline-success me-1" title="Listo"><i class="fas fa-check"></i></button>`;
            if (rolActual === 'Supervisor') acciones += `<button onclick="eliminarReporte('${key}')\" class="btn btn-sm btn-outline-danger" title="Eliminar"><i class="fas fa-trash-alt"></i></button>`;
        }

        const html = `<tr id="${key}" class="${data.estado === "Completado" ? "table-success bg-opacity-25" : ""}">
            <td class="fw-bold text-dark">${data.unidad}</td><td>${badges}</td><td>${data.fecha}<br><small class="text-muted">${data.hora}</small></td>
            <td>${data.estado === "Completado" ? '<span class="badge rounded-pill bg-success">Listo</span>' : '<span class="badge rounded-pill bg-secondary">Pendiente</span>'}</td>
            <td>${acciones}</td></tr>`;
        document.getElementById('tablaCuerpo').insertAdjacentHTML('afterbegin', html);
    }'''

new_crear_fila = '''    function crearFila(key, data) {
        const prioridad = data.prioridad || 'media';
        const prioridadEmoji = {'baja':'🟢','media':'🟡','alta':'🟠','urgente':'🔴'}[prioridad];
        const prioridadTexto = {'baja':'Baja','media':'Media','alta':'Alta','urgente':'Urgente'}[prioridad];
        const prioridadClase = `prioridad-${prioridad}`;
        const filaClase = `fila-${prioridad}`;
        
        let badges = (data.fallas || []).map(f => `<span class="badge rounded-pill ${f === 'GPS' ? 'bg-danger' : f === 'RFID' ? 'bg-warning text-dark' : f === 'NVR' ? 'bg-info text-dark' : 'bg-success'} badge-falla border border-light shadow-sm">${f}</span>`).join('');
        let acciones = `<button onclick="mostrarObservaciones('${(data.observaciones || '').replace(/'/g, "\\\\'")}')\" class="btn btn-sm btn-outline-info me-1 border-0"><i class="fas fa-eye"></i></button>`;

        if (rolActual === 'Técnico' || rolActual === 'Supervisor') {
            if (data.estado !== "Completado") acciones += `<button onclick="marcarCompletado('${key}')\" class="btn btn-sm btn-outline-success me-1" title="Listo"><i class="fas fa-check"></i></button>`;
            if (rolActual === 'Supervisor') acciones += `<button onclick="eliminarReporte('${key}')\" class="btn btn-sm btn-outline-danger" title="Eliminar"><i class="fas fa-trash-alt"></i></button>`;
        }

        const html = `<tr id="${key}" class="${data.estado === "Completado" ? "table-success bg-opacity-25" : ""} ${filaClase}" data-prioridad="${prioridad}">
            <td class="fw-bold text-dark">${data.unidad}</td>
            <td>${badges}</td>
            <td>${data.fecha}<br><small class="text-muted">${data.hora}</small></td>
            <td><span class="prioridad-badge ${prioridadClase}">${prioridadEmoji} ${prioridadTexto}</span></td>
            <td>${data.estado === "Completado" ? '<span class="badge rounded-pill bg-success">Listo</span>' : '<span class="badge rounded-pill bg-secondary">Pendiente</span>'}</td>
            <td>${acciones}</td></tr>`;
        document.getElementById('tablaCuerpo').insertAdjacentHTML('afterbegin', html);
        
        // Ordenar por prioridad automáticamente
        ordenarTablaPorPrioridad();
    }
    
    function ordenarTablaPorPrioridad() {
        const tbody = document.getElementById('tablaCuerpo');
        const filas = Array.from(tbody.querySelectorAll('tr'));
        const prioridadOrden = {'urgente': 0, 'alta': 1, 'media': 2, 'baja': 3};
        
        filas.sort((a, b) => {
            const prioA = a.dataset.prioridad || 'media';
            const prioB = b.dataset.prioridad || 'media';
            return prioridadOrden[prioA] - prioridadOrden[prioB];
        });
        
        filas.forEach(fila => tbody.appendChild(fila));
    }'''

content = content.replace(old_crear_fila, new_crear_fila)

# Write back
with open(r'c:\Users\jrg23\OneDrive\Documentos\Antigravity\Reparaciones\index.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("JavaScript functionality updated successfully!")
