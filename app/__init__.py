# app/__init__.py
from flask import Flask
from pymongo import MongoClient
import os

# Declaramos variables globales para la conexión
mongo_client = None
db_mongo = None

def create_app():
    global mongo_client, db_mongo
    app = Flask(__name__)

    # 1. Conexión limpia al contenedor de MongoDB en Docker
    mongo_client = MongoClient("mongodb://localhost:27017/")
    db_mongo = mongo_client["tutor_inteligente_db"]
    
    # Exponemos la base de datos en la configuración de Flask para que los controladores la usen
    app.config["MONGO_DB"] = db_mongo

    # 2. Registro del Blueprint de tus controladores
    from app.controllers.main_controller import main_bp
    app.register_blueprint(main_bp)

    return app