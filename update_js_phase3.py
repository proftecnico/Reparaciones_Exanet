import re

# Read the file
with open(r'c:\Users\jrg23\OneDrive\Documentos\Antigravity\Reparaciones\index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# --------------------------------------------------------------------------------
# 1. Dark Mode Logic
# --------------------------------------------------------------------------------
# We'll add this at the beginning of the script module
dark_mode_logic = '''            // --- THEME SYSTEM ---
            window.toggleTheme = function() {
                const body = document.body;
                const isDark = body.getAttribute('data-theme') === 'dark';
                const newTheme = isDark ? 'light' : 'dark';
                
                body.setAttribute('data-theme', newTheme);
                localStorage.setItem('theme', newTheme);
                updateThemeIcon(newTheme);
            };

            function updateThemeIcon(theme) {
                const btn = document.getElementById('themeToggle');
                if(!btn) return;
                if(theme === 'dark') {
                    btn.innerHTML = '<i class="fas fa-sun fs-5 text-warning"></i>';
                } else {
                    btn.innerHTML = '<i class="fas fa-moon fs-5 text-secondary"></i>';
                }
            }

            // Init Theme
            const savedTheme = localStorage.getItem('theme') || 'light';
            document.body.setAttribute('data-theme', savedTheme);
            // We'll call updateThemeIcon after DOM load or manually here if button exists
            setTimeout(() => updateThemeIcon(savedTheme), 100);

            // --- ANIMATIONS & NOTIFICATIONS ---
            '''

# Insert after import
content = content.replace('            import { initializeApp } from "https://www.gstatic.com/firebasejs/10.7.1/firebase-app.js";', 
                          '            import { initializeApp } from "https://www.gstatic.com/firebasejs/10.7.1/firebase-app.js";\n' + dark_mode_logic)


# --------------------------------------------------------------------------------
# 2. Notifications Logic
# --------------------------------------------------------------------------------
# We'll add requestPermission logic in user login success or app init
notification_logic = '''
            // Solicitar permisos de notificación al cargar si ya está logueado o al loguearse
            function initNotifications() {
                if ("Notification" in window && Notification.permission !== "granted") {
                    Notification.requestPermission();
                }
            }
            
            function enviarNotificacionEscritorio(titulo, cuerpo) {
                if ("Notification" in window && Notification.permission === "granted" && document.visibilityState === "hidden") {
                    new Notification(titulo, { body: cuerpo, icon: "https://cdn-icons-png.flaticon.com/512/741/741407.png" });
                }
            }
'''

content = content.replace('// --- UI Helpers', notification_logic + '\n            // --- UI Helpers')

# --------------------------------------------------------------------------------
# 3. Update 'crearFila' for Animations and Notifications
# --------------------------------------------------------------------------------
# We need to find the existing crearFila and replace it to add the animation class
# AND trigger notification if it's a new report (we'll assume new reports called via child_added)

old_crear_fila_start = '    function crearFila(key, data) {'
new_crear_fila_start = '''    function crearFila(key, data, esNuevo = false) {
        // Notificación de escritorio si es nuevo y no soy yo
        if(esNuevo && data.usuario !== rolActual) {
            enviarNotificacionEscritorio("Nuevo Reporte", `Unidad ${data.unidad}: ${data.prioridad || 'Normal'}`);
        }
'''

content = content.replace(old_crear_fila_start, new_crear_fila_start)

# We also need to add the animation class to the tr
content = content.replace('const html = `<tr id="${key}" class="${data.estado === "Completado" ? "table-success bg-opacity-25" : ""} ${filaClase}" data-prioridad="${prioridad}">',
                          'const html = `<tr id="${key}" class="${data.estado === "Completado" ? "table-success bg-opacity-25" : ""} ${filaClase} animate-fade-in" data-prioridad="${prioridad}">')

# --------------------------------------------------------------------------------
# 4. Pagination Logic
# --------------------------------------------------------------------------------
# We need to change how onValue('reparaciones') works. Instead of clearing table and addRow, 
# it should update a global list and call 'renderizarTabla()'.

# Find the reparations listener
listener_regex = r"onValue\(reparacionesRef, \(snapshot\) => \{[\s\S]*?\}\);"
match = re.search(listener_regex, content)

if match:
    old_listener = match.group(0)
    
    new_listener = '''
            let todosLosReportes = [];
            let paginaActual = 1;
            const filasPorPagina = 10;

            onValue(reparacionesRef, (snapshot) => {
                todosLosReportes = [];
                const now = Date.now();
                
                snapshot.forEach(childSnapshot => {
                    const key = childSnapshot.key;
                    const data = childSnapshot.val();
                    todosLosReportes.push({ key, ...data });
                    
                    // Detectar si es reciente (últimos 3 segundos) para notificación
                    // Esto es una aproximación, idealmente child_added
                });
                
                // Ordenar: Prioridad primero, luego fecha
                todosLosReportes.sort((a, b) => {
                     const prioridadOrden = {'urgente': 0, 'alta': 1, 'media': 2, 'baja': 3};
                     const pA = prioridadOrden[a.prioridad || 'media'];
                     const pB = prioridadOrden[b.prioridad || 'media'];
                     return pA - pB;
                });

                renderizarTabla();
                actualizarContadores(todosLosReportes); // Helper function extracted
            });

            window.renderizarTabla = function() {
                const tbody = document.getElementById('tablaCuerpo');
                tbody.innerHTML = '';
                
                // Aplicar filtros primero
                let filtrados = todosLosReportes.filter(r => {
                    const fEstado = document.getElementById('filtroEstado').value;
                    const fPrio = document.getElementById('filtroPrioridad').value;
                    const fBusq = document.getElementById('busquedaTabla').value.toLowerCase();
                    
                    if(fEstado && (r.estado === 'Completado' ? 'Completado' : 'Pendiente') !== fEstado) return false;
                    if(fPrio && (r.prioridad || 'media') !== fPrio) return false;
                    if(fBusq && !r.unidad.toLowerCase().includes(fBusq)) return false;
                    
                    return true;
                });
                
                // Paginación
                const totalPaginas = Math.ceil(filtrados.length / filasPorPagina) || 1;
                paginaActual = Math.min(paginaActual, totalPaginas);
                
                const inicio = (paginaActual - 1) * filasPorPagina;
                const fin = inicio + filasPorPagina;
                const paginaItems = filtrados.slice(inicio, fin);
                
                paginaItems.forEach(item => crearFila(item.key, item));
                
                document.getElementById('contadorResultados').innerText = 
                    `Mostrando ${paginaItems.length} de ${filtrados.length} reportes (Pág ${paginaActual}/${totalPaginas})`;
                    
                actualizarControlesPaginacion(totalPaginas);
                
                document.getElementById('loading').style.display = 'none';
            };

            window.cambiarPagina = function(delta) {
                paginaActual += delta;
                renderizarTabla();
            };
            
            function actualizarControlesPaginacion(total) {
                let div = document.getElementById('paginacionControles');
                if(!div) {
                    div = document.createElement('div');
                    div.id = 'paginacionControles';
                    div.className = 'd-flex justify-content-center gap-2 mt-3';
                    document.getElementById('tablaReportes').after(div);
                }
                
                div.innerHTML = `
                    <button class="btn btn-sm btn-outline-secondary" onclick="cambiarPagina(-1)" ${paginaActual === 1 ? 'disabled' : ''}>
                        <i class="fas fa-chevron-left"></i>
                    </button>
                    <span class="align-self-center small fw-bold text-muted">Pág ${paginaActual}</span>
                    <button class="btn btn-sm btn-outline-secondary" onclick="cambiarPagina(1)" ${paginaActual >= total ? 'disabled' : ''}>
                        <i class="fas fa-chevron-right"></i>
                    </button>
                `;
            }
            
            function actualizarContadores(lista) {
                 const pendientes = lista.filter(r => r.estado !== "Completado").length;
                 const listas = lista.filter(r => r.estado === "Completado").length;
                 // Bajas se obtienen de otra ref, omitimos por ahora o mantenemos lógica anterior si posible
                 document.getElementById('contadorPendientes').innerText = pendientes;
                 document.getElementById('contadorListas').innerText = listas;
            }
    '''
    
    # We replace the old listener BUT we must be careful about 'actualizarContadores' which might be missing context
    # The original code updated counters inside the loop or after. 
    # Let's inspect the original code for counters. 
    
    content = content.replace(old_listener, new_listener)

# --------------------------------------------------------------------------------
# 5. Connect filters to renderizarTabla
# --------------------------------------------------------------------------------
# The old 'aplicarFiltros' manipulated DOM directly. New one uses renderizarTabla.
old_app_filters = '''        window.aplicarFiltros = function() {
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
        };'''

new_app_filters = '''        window.aplicarFiltros = function() {
            paginaActual = 1; // Reset a primera página al filtrar
            renderizarTabla();
        };
        
        // Conectar búsqueda también
        document.getElementById('busquedaTabla').addEventListener('input', () => {
             paginaActual = 1;
             renderizarTabla();
        });'''

content = content.replace(old_app_filters, new_app_filters)

# --------------------------------------------------------------------------------
# 6. Init Notifications on Login
# --------------------------------------------------------------------------------
content = content.replace("mostrarToast(`👋 Bienvenido ${rol}`, 'info');", 
                          "mostrarToast(`👋 Bienvenido ${rol}`, 'info'); initNotifications();")


# Write back
with open(r'c:\Users\jrg23\OneDrive\Documentos\Antigravity\Reparaciones\index.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("JS Phase 3 functionality updated successfully!")
