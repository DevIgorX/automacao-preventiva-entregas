from extension import db

class Usuarios(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nome = db.Column(db.String(), nullable=False)
    email = db.Column(db.String(), nullable=False)
    senha = db.Column(db.String(100),nullable=False)

    def __repr__(self):
        return '<Name %r>' % self.nome
