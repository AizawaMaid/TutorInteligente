Paso1: Intalación de base de datos no relacional:

sudo apt update
sudo apt install -y mongodb
# Iniciar y habilitar el servicio
sudo systemctl start mongodb
sudo systemctl enable mongodb

Paso 2: Clona o descarga este repositorio en tu máquina local y colócate dentro de la carpeta raíz del proyecto.
ejemplo: cd TutorInteligente

Paso 3 (opcional): Crea un entorno virtual y activalo
  # En Windows:
  python -m venv venv
  
  # En macOS/Linux:
  python3 -m venv venv
  
  //////////////////////////////////////////////////////////////////////7
  # En Windows (Prompt de comandos):
  venv\\Scripts\\activate
  
  # En Windows (PowerShell):
  .\\venv\\Scripts\\activate.ps1
  
  # En macOS/Linux:
  source venv/bin/activate

Paso 4: Instalar dependencias paquetes como Flask, pymongo, rdflib.

Paso 5: Ejecuta la aplicación **python run.py**
