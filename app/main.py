from app import create_app
import os
from waitress import serve



app = create_app()

if __name__ == '__main__':
    # Pega a porta do ambiente ou usa 5000 como padrão
    port = int(os.environ.get("PORT", 5000))
    
    # Verifica se estamos em modo de Debug (configurado no seu .env/config.py)
    # Se DEBUG for True (seu PC), usa o servidor do Flask
    if app.config.get('DEBUG'):
        app.run(host='0.0.0.0', port=port)
    
    # Se DEBUG for False (Servidor de Produção), usa o Waitress
    else:
        print(f"Iniciando servidor de produção (Waitress) na porta {port}...")
        serve(app, host='0.0.0.0', port=port)