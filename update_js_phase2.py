import re

# Read the file
with open(r'c:\Users\jrg23\OneDrive\Documentos\Antigravity\Reparaciones\index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# --------------------------------------------------------------------------------
# 1. Update form submit to register history
# --------------------------------------------------------------------------------
old_submit_block = '''            push(dbRef, {
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
            });'''

new_submit_block = '''            const nuevoRef = push(dbRef);
            const fechaHoy = new Date().toLocaleDateString('es-AR');
            const horaHoy = new Date().toLocaleTimeString('es-AR', { hour: '2-digit', minute: '2-digit' });
            
            set(nuevoRef, {
                unidad: unidad, 
                fallas: listaFallas, 
                observaciones: obs,
                prioridad: prioridad,
                fecha: fechaHoy, 
                hora: horaHoy,
                estado: "Pendiente", 
                usuario: rolActual
            }).then(() => {
                // Registrar Historial Inicial
                push(ref(db, `reparaciones/${nuevoRef.key}/historial`), {
                    accion: "Creación de reporte",
                    usuario: rolActual,
                    fecha: fechaHoy,
                    hora: horaHoy
                });
                
                mostrarToast('✅ Reporte enviado.', 'success'); 
                document.getElementById('reporteForm').reset();
                document.getElementById('panelFallas').style.display = 'none'; 
                document.getElementById('selectorUnidad').disabled = true;
                document.getElementById('selectorUnidad').innerHTML = '<option value="">-- Primero elija grupo --</option>';
                document.getElementById('selectorPrioridad').classList.remove('is-valid');
            });'''

content = content.replace(old_submit_block, new_submit_block)

# --------------------------------------------------------------------------------
# 2. Update marcarCompletado to register history
# --------------------------------------------------------------------------------
old_complete = '''        window.marcarCompletado = function (id) {
            if (confirm("¿Confirmar reparación completada?")) {
                update(ref(db, 'reparaciones/' + id), { estado: "Completado", fechaResolucion: new Date().toLocaleDateString('es-AR') })
                    .then(() => mostrarToast('👍 Reparación completada.', 'success'));
            }
        };'''

new_complete = '''        window.marcarCompletado = function (id) {
            if (confirm("¿Confirmar reparación completada?")) {
                const fechaHoy = new Date().toLocaleDateString('es-AR');
                const horaHoy = new Date().toLocaleTimeString('es-AR', { hour: '2-digit', minute: '2-digit' });
                
                update(ref(db, 'reparaciones/' + id), { estado: "Completado", fechaResolucion: fechaHoy })
                    .then(() => {
                        push(ref(db, `reparaciones/${id}/historial`), {
                            accion: "Reparación completada",
                            usuario: rolActual,
                            fecha: fechaHoy,
                            hora: horaHoy
                        });
                        mostrarToast('👍 Reparación completada.', 'success');
                    });
            }
        };'''

content = content.replace(old_complete, new_complete)

# --------------------------------------------------------------------------------
# 3. Replace mostrarObservaciones with abrirDetalles and logic
# --------------------------------------------------------------------------------
# We remove the old function and insert all new logic
old_obs_func = '''        window.mostrarObservaciones = function (obs) {
            document.getElementById('modalContenido').innerText = obs || 'Sin observaciones.';
            new bootstrap.Modal(document.getElementById('modalObservaciones')).show();
        };'''

new_logic = '''        // --- GESTIÓN DETALLES (COMENTARIOS Y TIMELINE) ---
        let reporteActualId = null;

        window.mostrarObservaciones = function(id) {
            abrirDetalles(id); // Compatibilidad con botones viejos
        };

        window.abrirDetalles = function(id) {
            reporteActualId = id;
            const modal = new bootstrap.Modal(document.getElementById('modalDetalles'));
            
            // Listeners para este reporte
            const reporteRef = ref(db, `reparaciones/${id}`);
            
            get(reporteRef).then((snapshot) => {
                if(snapshot.exists()) {
                    const data = snapshot.val();
                    
                    // Cargar Info General
                    document.getElementById('detalleBadgeUnidad').innerText = `Unidad ${data.unidad}`;
                    
                    const prio = data.prioridad || 'media';
                    const prioEmoji = {'baja':'🟢','media':'🟡','alta':'🟠','urgente':'🔴'}[prio];
                    document.getElementById('detalleBadgePrioridad').innerHTML = `${prioEmoji} ${prio.toUpperCase()}`;
                    
                    document.getElementById('detalleFecha').innerText = data.fecha;
                    document.getElementById('detalleHora').innerText = data.hora;
                    document.getElementById('detalleUsuario').innerText = data.usuario || 'Desconocido';
                    document.getElementById('detalleObservacion').innerText = data.observaciones || 'Sin observaciones';
                    
                    const containerFallas = document.getElementById('detalleFallas');
                    containerFallas.innerHTML = '';
                    (data.fallas || []).forEach(f => {
                         containerFallas.innerHTML += `<span class="badge bg-secondary border">${f}</span>`;
                    });

                    // Cargar Historial y Comentarios
                    cargarHistorial(id);
                    cargarComentarios(id);
                    
                    modal.show();
                }
            });
        };

        function cargarHistorial(id) {
            const container = document.getElementById('timelineContainer');
            onValue(ref(db, `reparaciones/${id}/historial`), (snapshot) => {
                container.innerHTML = '';
                if(snapshot.exists()) {
                    snapshot.forEach(child => {
                        const h = child.val();
                        container.innerHTML += `
                            <div class="timeline-item">
                                <span class="timeline-date">${h.fecha} - ${h.hora}</span>
                                <div class="timeline-content">
                                    <strong>${h.accion}</strong><br>
                                    <small class="text-muted">Por: ${h.usuario}</small>
                                </div>
                            </div>`;
                    });
                } else {
                    container.innerHTML = '<p class="text-muted text-center mt-3">No hay historial registrado.</p>';
                }
            });
        }

        function cargarComentarios(id) {
            const container = document.getElementById('listaComentarios');
            onValue(ref(db, `reparaciones/${id}/comentarios`), (snapshot) => {
                container.innerHTML = '';
                if(snapshot.exists()) {
                    let hasComments = false;
                    snapshot.forEach(child => {
                        hasComments = true;
                        const c = child.val();
                        const esMio = c.usuario === rolActual;
                        container.innerHTML += `
                            <div class="chat-bubble ${esMio ? 'me' : 'other'}">
                                <div class="chat-meta">${c.usuario} - ${c.hora}</div>
                                ${c.texto}
                            </div>`;
                    });
                    container.scrollTop = container.scrollHeight;
                } else {
                    container.innerHTML = '<div class="text-center text-muted py-5"><i class="fas fa-comment-slash fa-2x mb-2"></i><br>No hay comentarios aún</div>';
                }
            });
        }

        window.enviarComentario = function() {
            const input = document.getElementById('inputNuevoComentario');
            const texto = input.value.trim();
            if(!texto || !reporteActualId) return;
            
            push(ref(db, `reparaciones/${reporteActualId}/comentarios`), {
                texto: texto,
                usuario: rolActual,
                fecha: new Date().toLocaleDateString('es-AR'),
                hora: new Date().toLocaleTimeString('es-AR', { hour: '2-digit', minute: '2-digit' })
            }).then(() => input.value = '');
        };
        
        // --- EXPORTACIÓN PDF ---
        window.descargarPDF = function() {
            const elemento = document.createElement('div');
            elemento.innerHTML = `
                <div style="padding: 20px; font-family: sans-serif;">
                    <div style="text-align: center; margin-bottom: 20px; border-bottom: 2px solid #333; padding-bottom: 10px;">
                        <h1 style="margin: 0;">🚛 Reporte de Flota</h1>
                        <p>Generado el: ${new Date().toLocaleDateString('es-AR')}</p>
                    </div>
                    <div style="margin-bottom: 20px;">
                        <h3>Resumen</h3>
                        <p>Pendientes: ${document.getElementById('contadorPendientes').innerText} | 
                           Completadas: ${document.getElementById('contadorListas').innerText} | 
                           Bajas: ${document.getElementById('contadorBajas').innerText}</p>
                    </div>
                    <div>
                        <h3>Detalle de Reparaciones</h3>
                        <table style="width: 100%; border-collapse: collapse; font-size: 12px;">
                            <thead style="background: #333; color: white;">
                                <tr>
                                    <th style="padding: 8px;">Unidad</th>
                                    <th style="padding: 8px;">Prioridad</th>
                                    <th style="padding: 8px;">Fallas</th>
                                    <th style="padding: 8px;">Estado</th>
                                    <th style="padding: 8px;">Fecha</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${Array.from(document.querySelectorAll('#tablaCuerpo tr')).map(tr => {
                                    if(tr.style.display === 'none') return ''; // Solo exportar lo visible
                                    const tds = tr.querySelectorAll('td');
                                    // Limpiar badges para texto plano
                                    const unidad = tds[0].innerText;
                                    const fallas = tds[1].innerText.replace(/\n/g, ', ');
                                    const fecha = tds[2].innerText.split('\n')[0];
                                    const prio = tds[3].innerText;
                                    const estado = tds[4].innerText;
                                    
                                    return `
                                    <tr style="border-bottom: 1px solid #ddd;">
                                        <td style="padding: 8px;">${unidad}</td>
                                        <td style="padding: 8px;">${prio}</td>
                                        <td style="padding: 8px;">${fallas}</td>
                                        <td style="padding: 8px;">${estado}</td>
                                        <td style="padding: 8px;">${fecha}</td>
                                    </tr>`;
                                }).join('')}
                            </tbody>
                        </table>
                    </div>
                </div>
            `;

            const opt = {
                margin: 10,
                filename: 'Reporte_Flota_Completo.pdf',
                image: { type: 'jpeg', quality: 0.98 },
                html2canvas: { scale: 2 },
                jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' }
            };

            html2pdf().set(opt).from(elemento).save();
        };'''

content = content.replace(old_obs_func, new_logic)

# --------------------------------------------------------------------------------
# 4. Update element attributes in created table rows (to call abrirDetalles instead of mostrarObservaciones)
# --------------------------------------------------------------------------------
old_btn_obs = "let acciones = `<button onclick=\"mostrarObservaciones('${(data.observaciones || '').replace(/'/g, \"\\\\'\")}')\" class=\"btn btn-sm btn-outline-info me-1 border-0\"><i class=\"fas fa-eye\"></i></button>`;"
new_btn_obs = "let acciones = `<button onclick=\"abrirDetalles('${key}')\" class=\"btn btn-sm btn-outline-info me-1 border-0\"><i class=\"fas fa-eye\"></i></button>`;"

content = content.replace(old_btn_obs, new_btn_obs)

# Write back
with open(r'c:\Users\jrg23\OneDrive\Documentos\Antigravity\Reparaciones\index.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("JS Phase 2 functionality updated successfully!")
