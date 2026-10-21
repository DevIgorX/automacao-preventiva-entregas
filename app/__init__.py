from flask import Flask
from flask_wtf.csrf import CSRFProtect
from .routes import rotas  # Importa o blueprint de rotas

crsf = CSRFProtect()
def create_app():
    app = Flask(__name__)

    # Carrega configurações
    app.config.from_pyfile('config.py')

    # crsf.init_app(app)
    app.config['WTF_CSRF_ENABLED'] = False
    # Registra os blueprints
    app.register_blueprint(rotas)

    from .cruzamento import init_app as init_cruzamento
    init_cruzamento(app)

    return app
