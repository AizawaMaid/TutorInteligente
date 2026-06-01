from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client["tutor_inteligente_db"]
coleccion = db["estudiantes"]

# 1. Limpiamos por completo la colección anterior
coleccion.delete_many({})

# 2. Tu documento ideal estructurado correctamente
mis_estudiantes = [
    {
        "_id": "carolina_j",
        "nombre_completo": "Carolina Jaramillo Herrera",
        "semestre_actual": 6,
        "intereses": {
            "area": "Inteligencia_Artificial",
            "materias_interes": ["Aprendizaje_Automatico", "Redes_Neuronales"]
        }, 
        "materias_aprobadas": [
            {"nombre": "Introduccion_a_la_Programacion", "semestre_actual": 1, "area": "Programacion", "tipo": "Obligatoria", "prerrequisitos": []},
            {"nombre": "Matematicas_Discretas", "semestre_actual": 2, "area": "Matematicas", "tipo": "Obligatoria", "prerrequisitos": ["Introduccion_a_la_Programacion"]},
            {"nombre": "Algebra_Lineal", "semestre_actual": 4, "area": "Matematicas", "tipo": "Obligatoria", "prerrequisitos": ["Matematicas_Discretas"]}
        ],
        "materias_no_aprobadas": [
            {"nombre": "Calculo_I", "semestre_actual": 3, "area": "Matematicas", "tipo": "Obligatoria", "prerrequisitos": ["Matematicas_Discretas"]},
            {"nombre": "Calculo_II", "semestre_actual": 5, "area": "Matematicas", "tipo": "Obligatoria", "prerrequisitos": ["Calculo_I"]}
        ]
    } 
]

# 3. Insertamos el documento ideal
coleccion.insert_many(mis_estudiantes)
print("¡Estudiantes de prueba creados con éxito!")