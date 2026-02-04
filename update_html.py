import re

# Read the file
with  open(r'c:\Users\jrg23\OneDrive\Documentos\Antigravity\Reparaciones\index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add priority column to table header (after Estado column)
content = content.replace(
    '<th>Estado <i class="fas fa-sort text-muted ms-1" style="cursor:pointer;" onclick="ordenarTabla(3)"></i></th>',
    '<th>Prioridad</th>\r\n                                    <th>Estado <i class="fas fa-sort text-muted ms-1" style="cursor:pointer;" onclick="ordenarTabla(3)"></i></th>'
)

# 2. Insert filters panel before table card
filters_panel = '''
        <!-- Panel de Filtros -->
        <div id="panelFiltros" style="display:none;">
            <div class="d-flex justify-content-between align-items-center mb-3">
                <h6 class="mb-0 fw-bold"><i class="fas fa-filter me-2"></i>Filtros Avanzados</h6>
                <button onclick="limpiarFiltros()" class="btn btn-sm btn-outline-secondary"><i class="fas fa-times me-1"></i>Limpiar</button>
            </div>
            <div class="filtros-grid">
                <div>
                    <label class="form-label small fw-bold">Estado</label>
                    <select class="form-select form-select-sm" id="filtroEstado" onchange="aplicarFiltros()">
                        <option value="">Todos</option>
                        <option value="Pendiente">Pendiente</option>
                        <option value="Completado">Completado</option>
                    </select>
                </div>
                <div>
                    <label class="form-label small fw-bold">Prioridad</label>
                    <select class="form-select form-select-sm" id="filtroPrioridad" onchange="aplicarFiltros()">
                        <option value="">Todas</option>
                        <option value="urgente">🔴 Urgente</option>
                        <option value="alta">🟠 Alta</option>
                        <option value="media">🟡 Media</option>
                        <option value="baja">🟢 Baja</option>
                    </select>
                </div>
            </div>
            <div class="mt-3 text-center">
                <span class="contador-resultados" id="contadorResultados">Mostrando todos los reportes</span>
            </div>
        </div>

'''

# Find and insert before the table card
pattern = r'(\s+<div class="card">[\r\n\s]+<div[\r\n\s]+class="card-header bg-dark text-white)'
content = re.sub(pattern, filters_panel + r'\1', content, count=1)

# 3. Add filter button to table header
old_header = '''<h5 class="mb-0"><i class="fas fa-list-alt me-2"></i>Reparaciones Pendientes</h5>
                    <div class="input-group input-group-sm mt-2 mt-md-0" style="max-width: 250px;">'''

new_header = '''<h5 class="mb-0"><i class="fas fa-list-alt me-2"></i>Reparaciones Pendientes</h5>
                    <div class="d-flex gap-2 align-items-center mt-2 mt-md-0">
                        <button onclick="toggleFiltros()" class="btn btn-sm btn-outline-light"><i class="fas fa-filter me-1"></i><span class="btn-texto">Filtros</span></button>
                        <div class="input-group input-group-sm" style="max-width: 250px;">'''

content = content.replace(old_header, new_header)

# Close the new div
content = content.replace(
    '</div>\r\n                </div>\r\n                <div class="card-body p-0">',
    '</div>\r\n                    </div>\r\n                </div>\r\n                <div class="card-body p-0">'
)

# Write back
with open(r'c:\Users\jrg23\OneDrive\Documentos\Antigravity\Reparaciones\index.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ HTML structure updated successfully!")
