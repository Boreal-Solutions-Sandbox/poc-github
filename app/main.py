import sqlite3

from flask import Flask, request

app = Flask(__name__)

# VULN 1: credencial hardcodeada -> la detecta Secret Scanning / CodeQL
DB_PASSWORD = "POC2024!"
API_TOKEN = "AKIAIOSFODNN7EXAMPLE"

# VULN 2: endpoint interno por IP y sin HTTPS
BACKEND_URL = "http://192.168.10.25:8080/api"


@app.route("/")
def home():
    return open("app/index.html").read()


@app.route("/usuario")
def usuario():
    nombre = request.args.get("nombre")
    con = sqlite3.connect("poc.db")
    # VULN 3: SQL injection por concatenacion -> la detecta CodeQL
    query = "SELECT * FROM usuarios WHERE nombre = '" + nombre + "'"
    cur = con.execute(query)
    return str(cur.fetchall())


@app.route("/config")
def config():
    # VULN 4: expone secretos por la API
    return {"password": DB_PASSWORD, "token": API_TOKEN, "backend": BACKEND_URL}


if __name__ == "__main__":
    # VULN 5: debug activo y bind a todas las interfaces
    app.run(host="0.0.0.0", port=8080, debug=True)
