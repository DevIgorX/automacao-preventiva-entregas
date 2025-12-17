from flask import Flask
# from flask_wtf.csrf import CSRFProtect
from .routes import rotas  # Importa o blueprint de rotas


def create_app():
    app = Flask(__name__)

    # Carrega configurações
    app.config.from_pyfile('config.py')

    # crsf = CSRFProtect(app)
    # Registra os blueprints
    app.register_blueprint(rotas)

    return app
