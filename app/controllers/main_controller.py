# app/controllers/main_controller.py
from flask import Blueprint, render_template, jsonify, request, current_app
from app.models.ontology_model import TutorInteligenteModel
import os

main_bp = Blueprint('main', __name__)

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
ONTOLOGY_PATH = os.path.join(BASE_DIR, '../../data/ontologiaProyectoFinal.rdf')

tutor_tto = None

def obtener_tutor_instancia():
    global tutor_tto
    if tutor_tto is None:
        db_mongo = current_app.config["MONGO_DB"]
        tutor_tto = TutorInteligenteModel(ONTOLOGY_PATH, db_mongo)
    return tutor_tto

@main_bp.route('/')
def index():
    tutor = obtener_tutor_instancia()
    lista_estudiantes = tutor.get_all_students()
    return render_template('index.html', estudiantes=lista_estudiantes)

@main_bp.route('/api/ontologia/catalogo')
def obtener_catalogo():
    tutor = obtener_tutor_instancia()
    catalogo = tutor.obtener_catalogo_materias()
    return jsonify(catalogo)

@main_bp.route('/api/tutor/recomendar')
def recomendar_materias():
    tutor = obtener_tutor_instancia()
    id_estudiante = request.args.get('estudiante')
    origen = request.args.get('origen', 'mongodb') # 'mongodb' o 'protege'
    
    if not id_estudiante:
        return jsonify({'error': 'Falta el ID del estudiante'}), 400
        
    analisis = tutor.obtener_recomendaciones_multicriterio(id_estudiante, origen)
    return jsonify(analisis)

@main_bp.route('/api/estudiante/guardar', methods=['POST'])
def guardar_estudiante():
    tutor = obtener_tutor_instancia()
    datos_estudiante = request.get_json()
    
    if not datos_estudiante or '_id' not in datos_estudiante or 'nombre_completo' not in datos_estudiante:
        return jsonify({'error': 'Estructura inválida.'}), 400
        
    try:
        id_guardado = tutor.guardar_estudiante_json(datos_estudiante)
        return jsonify({'success': True, 'id': id_guardado}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500