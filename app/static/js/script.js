// Guardará localmente el catálogo estructurado que viene de la ontología
        let catalogoFijo = { materias: [], areas: [] };

        // Al levantar el navegador, consultamos los catálogos fijos de la ontología
        document.addEventListener("DOMContentLoaded", () => {
            fetch('/api/ontologia/catalogo')
                .then(res => {
                    if (!res.ok) throw new Error("Error al recuperar el catálogo ontológico.");
                    return res.json();
                })
                .then(data => {
                    catalogoFijo = data;
                    
                    // 1. Poblamos el combo del Área de Interés
                    const selectArea = document.getElementById("formAreaInteres");
                    selectArea.innerHTML = '<option disabled selected value="">Seleccionar área...</option>';
                    data.areas.forEach(area => {
                        selectArea.innerHTML += `<option value="${area}">${area.replace(/_/g, ' ')}</option>`;
                    });

                    // 2. Poblamos las cajas de checkboxes fijas de asignaturas
                    const contAprobadas = document.getElementById("contenedorAprobadas");
                    const contNoAprobadas = document.getElementById("contenedorNoAprobadas");

                    data.materias.forEach(mat => {
                        const crearItemHTML = (tipoContenedor) => `
                            <div class="form-check py-1 border-bottom border-light">
                                <input class="form-check-input check-materia" type="checkbox" value="${mat.id}" 
                                       id="${tipoContenedor}_${mat.id}" 
                                       data-semestre="${mat.semestre}" 
                                       data-area="${mat.area}" 
                                       data-tipo="${mat.tipo}" 
                                       data-prereq='${JSON.stringify(mat.prerrequisitos)}'>
                                <label class="form-check-label small" for="${tipoContenedor}_${mat.id}">
                                    <span class="badge bg-secondary me-1">Sem ${mat.semestre}</span> ${mat.nombre_legible}
                                </label>
                            </div>`;
                        
                        contAprobadas.innerHTML += crearItemHTML('aprobada');
                        contNoAprobadas.innerHTML += crearItemHTML('no_aprobada');
                    });
                })
                .catch(err => console.error("[-] Error de inicialización:", err));
        });

        // Construye de manera limpia la estructura de tu "Documento Ideal" y lo manda a guardar
        function guardarPerfilIdeal(e) {
            e.preventDefault();

            const documentoIdeal = {
                "_id": document.getElementById("formId").value.trim().toLowerCase().replace(/\s+/g, '_'),
                "nombre_completo": document.getElementById("formNombre").value.trim(),
                "semestre_actual": parseInt(document.getElementById("formSemestre").value),
                "intereses": {
                    "area": document.getElementById("formAreaInteres").value,
                    "materias_interes": [] // Puede expandirse dinámicamente si se requiere
                },
                "materias_aprobadas": [],
                "materias_no_aprobadas": []
            };

            // Barremos el catálogo fijo para meter la data estructurada exacta
            catalogoFijo.materias.forEach(mat => {
                const cbAprobada = document.getElementById(`aprobada_${mat.id}`);
                if (cbAprobada && cbAprobada.checked) {
                    documentoIdeal.materias_aprobadas.push({
                        "nombre": mat.id,
                        "semestre_actual": mat.semestre,
                        "area": mat.area,
                        "tipo": mat.tipo,
                        "prerrequisitos": mat.prerrequisitos
                    });
                }

                const cbNoAprobada = document.getElementById(`no_aprobada_${mat.id}`);
                if (cbNoAprobada && cbNoAprobada.checked) {
                    documentoIdeal.materias_no_aprobadas.push({
                        "nombre": mat.id,
                        "semestre_actual": mat.semestre,
                        "area": mat.area,
                        "tipo": mat.tipo,
                        "prerrequisitos": mat.prerrequisitos
                    });
                }
            });

            // Enviamos el payload estructurado al Endpoint de persistencia NoSQL
            fetch('/api/estudiante/guardar', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(documentoIdeal)
            })
            .then(res => res.json())
            .then(resData => {
                if (resData.success) {
                    alert("¡Documento Ideal guardado y persistido con éxito en MongoDB!");
                    location.reload(); // Recarga la vista para pintar la opción en la lista
                } else {
                    alert("Ocurrió un inconveniente: " + resData.error);
                }
            })
            .catch(err => alert("Error de red al intentar guardar."));
        }

        // Pide al servidor computar las inferencias mandando el ID y el origen ('mongodb' o 'protege')
        function cargarRecomendaciones(estudianteId, origen) {
            const bloque = document.getElementById("bloqueResultados");
            const spinner = document.getElementById("spinner");

            spinner.classList.remove("d-none");
            bloque.innerHTML = `
                <div class="text-center text-muted py-5 shadow-sm rounded border bg-light my-3">
                    <div class="spinner-border text-primary mb-3" role="status"></div>
                    <p class="mb-0 fw-bold">Inyectando datos transitorios en memoria y ejecutando el razonador Pellet...</p>
                    <span class="small text-secondary">Evaluando reglas SWRL y jerarquías...</span>
                </div>`;

            // Hacemos el fetch mandando el origen del alumno seleccionado
            fetch(`/api/tutor/recomendar?estudiante=${estudianteId}&origen=${origen}`)
                .then(res => {
                    if (!res.ok) throw new Error("Error en el razonamiento.");
                    return res.json();
                })
                .then(analisis => {
                    spinner.classList.add("d-none");
                    bloque.innerHTML = '';

                    // Inyecta dinámicamente las cajitas con los resultados segmentados de las 4 reglas
                    const pintarBloqueRegla = (titulo, items, color, descripcion) => {
                        let html = `
                            <div class="card mb-3 border-${color} shadow-sm">
                                <div class="card-header bg-${color} text-white py-2 d-flex justify-content-between align-items-center">
                                    <span class="fw-bold"><i class="bi bi-journal-check"></i> ${titulo}</span>
                                    <span class="badge bg-light text-dark small font-monospace">${items.length} asignaturas</span>
                                </div>
                                <div class="card-body bg-light py-1"><small class="text-muted italic d-block py-1">${descripcion}</small></div>
                                <ul class="list-group list-group-flush small">`;
                        
                        if (!items || items.length === 0) {
                            html += `<li class="list-group-item text-muted fst-italic py-2 px-3">Ninguna asignatura clasificada bajo este criterio.</li>`;
                        } else {
                            items.forEach(materia => {
                                html += `<li class="list-group-item fw-semibold text-dark py-2 px-3">📘 ${materia}</li>`;
                            });
                        }
                        html += `</ul></div>`;
                        return html;
                    };

                    // Pintamos las 4 secciones correspondientes a las reglas planteadas
                    bloque.innerHTML += pintarBloqueRegla(
                        "Puede Inscribir (Prerrequisitos Cubiertos)", 
                        analisis.puede_inscribir, 
                        "success",
                        "Inferencia: El estudiante cumplió con la totalidad de los prerrequisitos asignados en la ontología."
                    );
                    
                    bloque.innerHTML += pintarBloqueRegla(
                        "Recomendación por Área de Interés", 
                        analisis.recomendacion_area, 
                        "primary",
                        "Inferencia: Materias optativas que coinciden semánticamente con las áreas declaradas en sus intereses."
                    );
                    
                    bloque.innerHTML += pintarBloqueRegla(
                        "Sugerencia por Rezago (Semestres Anteriores)", 
                        analisis.recomendacion_semestre, 
                        "warning",
                        "Inferencia: Asignaturas no cursadas cuyo semestre curricular es menor al del nivel actual del estudiante."
                    );
                    
                    bloque.innerHTML += pintarBloqueRegla(
                        "No Recomendada / Bloqueada (Prerrequisitos Reprobados)", 
                        analisis.no_recomienda, 
                        "danger",
                        "Inferencia: Asignaturas bloqueadas automáticamente porque algún prerrequisito directo figura en el historial de no aprobadas."
                    );
                })
                .catch(err => {
                    spinner.classList.add("d-none");
                    bloque.innerHTML = `
                        <div class="alert alert-danger text-center my-4">
                            ❌ Ocurrió un error al procesar el razonamiento. Verifica que los nombres de los individuos en MongoDB correspondan con tu archivo OWL.
                        </div>`;
                });
        }