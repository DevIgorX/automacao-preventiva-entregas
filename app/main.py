from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/')
def iniciar():
 return jsonify({'Mensagem': 'Olá bem vindo ao monitoramento de preventiva'})


if __name__ == '__main__':
    app.run(debug=True)