import os
import sqlite3

from flask import Flask, request

app = Flask(__name__)

# FIX: credenciales desde el entorno / GitHub Secrets
DB_PASSWORD = os.environ["DB_PASSWORD"]
API_TOKEN = os.environ["API_TOKEN"]

# FIX: endpoint por nombre y sobre HTTPS
BACKEND_URL = os.environ.get("BACKEND_URL", "https://backend.poc.internal/api")


@app.route("/")
def home():
    with open("app/index.html") as f:
        return f.read()


@app.route("/usuario")
def usuario():
    nombre = request.args.get("nombre", "")
    con = sqlite3.connect("poc.db")
    # FIX: consulta parametrizada
    cur = con.execute("SELECT * FROM usuarios WHERE nombre = ?", (nombre,))
    return str(cur.fetchall())


@app.route("/config")
def config():
    # FIX: no se exponen secretos
    return {"backend": BACKEND_URL, "estado": "ok"}


if __name__ == "__main__":
    # FIX: sin debug, bind a localhost
    app.run(host="127.0.0.1", port=8080, debug=False)
