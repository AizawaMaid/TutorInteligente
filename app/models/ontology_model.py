# app/models/ontology_model.py
from owlready2 import *
import os

class TutorInteligenteModel:
    def __init__(self, filepath, db_mongo):
        self.filepath = os.path.abspath(filepath)
        # Cargamos la ontología base
        self.onto = get_ontology(f"file://{self.filepath}").load()
        # Referencia obligatoria a tu base MongoDB
        self.coleccion_estudiantes = db_mongo["estudiantes"]
        
        # Obtenemos el Namespace por defecto para que coincida 100% con Protégé
        self.ns = self.onto.get_namespace(self.onto.base_iri)

    def get_all_students(self):
        """Combina los perfiles de MongoDB y los individuos ya existentes en Protégé."""
        lista_combinada = []
        
        # 1. Alumnos dinámicos desde MongoDB
        try:
            estudiantes_mongo = list(self.coleccion_estudiantes.find({}))
            for est in estudiantes_mongo:
                lista_combinada.append({
                    "id": est["_id"],
                    "nombre": f"[DB] {est.get('nombre_completo', est['_id'])}",
                    "origen": "mongodb"
                })
        except Exception as e:
            print(f"[-] Error al leer MongoDB: {e}")

        # 2. Individuos nativos dentro del OWL de Protégé
        clase_estudiante = self.ns.Estudiante
        if clase_estudiante:
            for individuo in clase_estudiante.instances():
                if not any(e["id"] == individuo.name for e in lista_combinada):
                    lista_combinada.append({
                        "id": individuo.name,
                        "nombre": f"[Protégé] {individuo.name.replace('_', ' ')}",
                        "origen": "protege"
                    })
                    
        return lista_combinada

    def guardar_estudiante_json(self, documento_estudiante):
        """Guarda o actualiza la estructura exacta del documento ideal en MongoDB."""
        documento_estudiante["_id"] = documento_estudiante["_id"].lower().strip().replace(" ", "_")
        self.coleccion_estudiantes.update_one(
            {"_id": documento_estudiante["_id"]},
            {"$set": documento_estudiante},
            upsert=True
        )
        return documento_estudiante["_id"]

    def obtener_catalogo_materias(self):
        """Extrae el catálogo fijo de materias y áreas de la ontología para la interfaz."""
        materias_lista = []
        areas_set = set()

        clase_materia = self.ns.Materia
        if clase_materia:
            for materia in clase_materia.instances():
                clases_padre = [c.name for c in materia.is_a if hasattr(c, 'name')]
                tipo = "Optativa" if ("Materia_Optativa" in clases_padre or "MateriaOptativa" in clases_padre) else "Obligatoria"
                
                semestre = 1
                if hasattr(materia, "materiaSemestre"):
                    val = getattr(materia, "materiaSemestre")
                    if val: semestre = val[0] if isinstance(val, list) else val

                area_nombre = "General"
                if hasattr(materia, "tiene"):
                    areas_vinculadas = getattr(materia, "tiene")
                    if areas_vinculadas:
                        a_obj = areas_vinculadas[0] if isinstance(areas_vinculadas, list) else areas_vinculadas
                        if a_obj: 
                            area_nombre = a_obj.name
                            areas_set.add(a_obj.name)

                prereqs = []
                if hasattr(materia, "tienePrerrequisitos"):
                    p_vals = getattr(materia, "tienePrerrequisitos")
                    p_list = p_vals if isinstance(p_vals, list) else [p_vals]
                    prereqs = [p.name for p in p_list if p]

                materias_lista.append({
                    "id": materia.name,
                    "nombre_legible": materia.name.replace("_", " "),
                    "semestre": semestre,
                    "area": area_nombre,
                    "tipo": tipo,
                    "prerrequisitos": prereqs
                })

        clase_area = self.ns.Area
        if clase_area:
            for area in clase_area.instances():
                areas_set.add(area.name)

        return {
            "materias": sorted(materias_lista, key=lambda x: x["semestre"]),
            "areas": sorted(list(areas_set))
        }

    def obtener_recomendaciones_multicriterio(self, id_estudiante, origen):
        """
        Ejecuta el razonador Pellet garantizando la resolución nativa de propiedades
        mediante el Namespace de la ontología para activar todas las reglas SWRL.
        Incluye un filtro estricto para no recomendar materias que ya fueron aprobadas.
        """
        resultados = {
            "recomendacion_area": [],      # Regla 1 (Vocacional Nueva)
            "no_recomienda": [],           # Regla 2 (Bloqueadas)
            "recomendacion_semestre": [],   # Regla 3 (Rezago)
            "puede_inscribir": []          # Regla 4 (Prerrequisitos Válidos Nueva)
        }

        estudiante_semantico = None

        with self.onto:
            # Traer las clases y propiedades directamente desde el Namespace de tu OWL
            Estudiante = self.ns.Estudiante
            aprobo = self.ns.aprobo
            noAprobo = self.ns.noAprobo
            interesadoEn = self.ns.interesadoEn
            semestreActual = self.ns.semestreActual

            # --- CASO A: EL ALUMNO VIENE DE MONGODB ---
            if origen == "mongodb":
                alumno_doc = self.coleccion_estudiantes.find_one({"_id": id_estudiante.lower().strip()})
                if not alumno_doc:
                    return resultados

                # Instanciamos el individuo en el Namespace correcto
                estudiante_semantico = Estudiante(alumno_doc["_id"])
                
                # Inyectar Data Property: semestreActual
                if semestreActual:
                    semestre_val = int(alumno_doc.get("semestre_actual", 1))
                    getattr(estudiante_semantico, semestreActual.name).append(semestre_val)
                
                # Inyectar Object Property: interesadoEn (Área de interés)
                intereses_data = alumno_doc.get("intereses", {})
                area_id = intereses_data.get("area")
                if interesadoEn and area_id:
                    area_obj = getattr(self.ns, area_id, None)
                    if area_obj:
                        getattr(estudiante_semantico, interesadoEn.name).append(area_obj)

                # Inyectar Object Property: aprobo (Historial aprobadas)
                if aprobo:
                    for mat in alumno_doc.get("materias_aprobadas", []):
                        mat_obj = getattr(self.ns, mat['nombre'], None)
                        if mat_obj:
                            getattr(estudiante_semantico, aprobo.name).append(mat_obj)

                # Inyectar Object Property: noAprobo (Historial reprobadas)
                if noAprobo:
                    for mat in alumno_doc.get("materias_no_aprobadas", []):
                        mat_obj = getattr(self.ns, mat['nombre'], None)
                        if mat_obj:
                            getattr(estudiante_semantico, noAprobo.name).append(mat_obj)

            # --- CASO B: EL ALUMNO YA EXISTE EN PROTÉGÉ ---
            else:
                estudiante_semantico = getattr(self.ns, id_estudiante, None)
                if not estudiante_semantico:
                    print(f"[-] Individuo nativo no hallado en el OWL: {id_estudiante}")
                    return resultados

            # --- CORRER EL MOTOR DE INFERENCIA PELLET ---
            try:
                print(f"[+] Desplegando Pellet para resolver axiomas de: {estudiante_semantico.name}")
                sync_reasoner_pellet(infer_property_values=True, infer_data_property_values=True)
                print("[+] Inferencia semántica completada con éxito.")
            except Exception as e:
                print(f"[-] Incidente al ejecutar Pellet: {e}")

            # --- LEER LAS INFERENCIAS DE LAS REGLAS RELECTURAS (PELLET) ---
            
            # Intento de lectura directa de Pellet para puedeIncribir
            puedeIncribir_prop = self.ns.puedeIncribir
            if puedeIncribir_prop and hasattr(estudiante_semantico, puedeIncribir_prop.name):
                for mat in getattr(estudiante_semantico, puedeIncribir_prop.name):
                    resultados["puede_inscribir"].append(mat.name.replace("_", " "))

            # Intento de lectura directa de Pellet para recomendacionArea
            recomendacionArea_prop = getattr(self.ns, "recomendacionArea", None)
            if recomendacionArea_prop and hasattr(estudiante_semantico, recomendacionArea_prop.name):
                for mat in getattr(estudiante_semantico, recomendacionArea_prop.name):
                    resultados["recomendacion_area"].append(mat.name.replace("_", " "))

            # Regla 2: noRecomienda
            noRecomienda_prop = getattr(self.ns, "noRecomienda", None)
            if noRecomienda_prop and hasattr(estudiante_semantico, noRecomienda_prop.name):
                for mat in getattr(estudiante_semantico, noRecomienda_prop.name):
                    resultados["no_recomienda"].append(mat.name.replace("_", " "))

            # Regla 3: recomendacionSemestre
            recomendacionSemestre_prop = getattr(self.ns, "recomendacionSemestre", None)
            if recomendacionSemestre_prop and hasattr(estudiante_semantico, recomendacionSemestre_prop.name):
                for mat in getattr(estudiante_semantico, recomendacionSemestre_prop.name):
                    resultados["recomendacion_semestre"].append(mat.name.replace("_", " "))

            # =========================================================================
            # --- MOTOR DE RESPALDO HÍBRIDO CON FILTRO DE APROBADAS ---
            # =========================================================================
            
            lista_aprobadas = getattr(estudiante_semantico, "aprobo", [])
            lista_reprobadas = getattr(estudiante_semantico, "noAprobo", [])
            lista_intereses = getattr(estudiante_semantico, "interesadoEn", [])
            
            nombres_aprobadas = [m.name for m in lista_aprobadas if m]
            nombres_reprobadas = [m.name for m in lista_reprobadas if m]
            nombres_intereses = [a.name for a in lista_intereses if a]

            clase_materia = self.ns.Materia
            if clase_materia:
                for materia in clase_materia.instances():
                    # FILTRO CRÍTICO: Si la materia ya está aprobada, se ignora por completo
                    if materia.name in nombres_aprobadas:
                        continue

                    clases_padre = [c.name for c in materia.is_a if hasattr(c, 'name')]
                    
                    # Extraer prerrequisitos reales
                    lista_prereqs = []
                    if hasattr(materia, "tienePrerrequisitos"):
                        p_vals = getattr(materia, "tienePrerrequisitos")
                        lista_prereqs = p_vals if isinstance(p_vals, list) else [p_vals]
                        lista_prereqs = [p for p in lista_prereqs if p]

                    # Validar si aprobó todos los prerrequisitos
                    aprobó_prerrequisitos = False
                    if lista_prereqs:
                        aprobó_prerrequisitos = all(p.name in nombres_aprobadas for p in lista_prereqs)

                    # --- EVALUACIÓN DE LA REGLA DE PRERREQUISITOS NUEVA ---
                    # Recomienda si aprobó los requisitos Y está reprobada (o no cursada aún de forma limpia)
                    if aprobó_prerrequisitos and (materia.name in nombres_reprobadas or materia.name not in nombres_aprobadas):
                        mat_nombre_limpio = materia.name.replace("_", " ")
                        if mat_nombre_limpio not in resultados["puede_inscribir"]:
                            resultados["puede_inscribir"].append(mat_nombre_limpio)

                    # --- EVALUACIÓN DE LA REGLA DE ÁREA (VOCACIONAL) ---
                    es_optativa = "Materia_Optativa" in clases_padre or "MateriaOptativa" in clases_padre
                    if es_optativa and aprobó_prerrequisitos:
                        if hasattr(materia, "tiene"):
                            areas_vinculadas = getattr(materia, "tiene")
                            lista_areas = areas_vinculadas if isinstance(areas_vinculadas, list) else [areas_vinculadas]
                            
                            if any(a.name in nombres_intereses for a in lista_areas if a):
                                opt_nombre_limpio = materia.name.replace("_", " ")
                                if opt_nombre_limpio not in resultados["recomendacion_area"]:
                                    resultados["recomendacion_area"].append(opt_nombre_limpio)

            # --- LIMPIEZA ADICIONAL EN LA SALIDA DE INFERENCIAS DE PELLET ---
            # Nos aseguramos de que lo que se devuelva en la lista final jamás colisione con el historial aprobado
            resultados["puede_inscribir"] = [m for m in resultados["puede_inscribir"] if m.replace(" ", "_") not in nombres_aprobadas]
            resultados["recomendacion_area"] = [m for m in resultados["recommendation_area"] if m.replace(" ", "_") not in nombres_aprobadas] if "recommendation_area" in resultados else [m for m in resultados["recomendacion_area"] if m.replace(" ", "_") not in nombres_aprobadas]

            for clave in resultados:
                resultados[clave] = list(set(resultados[clave]))

            # --- LIMPIEZA DEL ENTORNO TRANSITORIO (SÓLO MONGODB) ---
            if origen == "mongodb" and estudiante_semantico:
                destroy_entity(estudiante_semantico)

        return resultados