# run.py
from app import create_app

app = create_app()

if __name__ == '__main__':
    # debug=True recarga la página automáticamente cuando haces cambios en el código
    app.run(host='0.0.0.0', port=5000,debug=True)



