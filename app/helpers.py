from flask_wtf import FlaskForm
from wtforms import StringField, validators, SubmitField, PasswordField


class FormularioLogin(FlaskForm):
    nome = StringField('Usuário', [ validators.DataRequired(), validators.length(min=1, max=50)])
    senha = PasswordField('Senha', [ validators.DataRequired(), validators.length(min=1, max=100)])
    entrar = SubmitField('Entrar')
