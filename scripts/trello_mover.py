#!/usr/bin/env python3
"""Mueve la tarjeta de Trello asociada a un ticket hacia una columna.

La tarjeta se identifica por el numero de ticket declarado en properties.yml:
  1. Campo personalizado del tablero (por defecto "Nº Ticket").
  2. Si no esta cargado, se busca el patron #NUMERO en el titulo de la tarjeta.
"""
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

API = "https://api.trello.com/1"

KEY = os.environ.get("TRELLO_KEY", "")
TOKEN = os.environ.get("TRELLO_TOKEN", "")
BOARD = os.environ.get("TRELLO_BOARD", "").strip()
TICKET = os.environ.get("TRELLO_TICKET", "").strip()
COLUMNA = os.environ.get("TRELLO_COLUMNA", "").strip()
CAMPO = os.environ.get("TRELLO_CAMPO", "Nº Ticket").strip()
COMENTARIO = os.environ.get("TRELLO_COMENTARIO", "").strip()


def fallar(msg):
    print(f"::error::{msg}")
    sys.exit(1)


def llamar(metodo, ruta, params=None):
    params = {**(params or {}), "key": KEY, "token": TOKEN}
    url = f"{API}{ruta}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, method=metodo)
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        fallar(f"Trello respondio {e.code} en {metodo} {ruta}: {e.read().decode()[:300]}")
    except Exception as e:
        fallar(f"No se pudo contactar a Trello: {e}")


def valor_campo(item):
    """Extrae el valor de un customFieldItem, sea texto, numero o fecha."""
    v = item.get("value")
    if isinstance(v, dict):
        for clave in ("text", "number", "date"):
            if v.get(clave) not in (None, ""):
                return str(v[clave]).strip()
    return None


def normalizar_ticket(texto):
    """Deja solo los digitos: '#507954' y '507954' se comparan igual."""
    return re.sub(r"\D", "", str(texto or ""))


def buscar_por_campo(tarjetas, id_campo, objetivo):
    for t in tarjetas:
        for item in t.get("customFieldItems", []) or []:
            if item.get("idCustomField") != id_campo:
                continue
            if normalizar_ticket(valor_campo(item)) == objetivo:
                return t
    return None


def buscar_por_titulo(tarjetas, objetivo):
    for t in tarjetas:
        m = re.search(r"#\s*(\d+)", t.get("name", ""))
        if m and m.group(1) == objetivo:
            return t
    return None


# ---------- Validaciones ----------
if not KEY or not TOKEN:
    fallar("Faltan los secrets TRELLO_KEY y/o TRELLO_TOKEN.")
if not BOARD:
    fallar("Falta TRELLO_BOARD (clave TableroTrello en properties.yml).")
if not TICKET:
    fallar("Falta TRELLO_TICKET (clave Ticket en properties.yml).")
if not COLUMNA:
    fallar("Falta TRELLO_COLUMNA (nombre de la columna destino).")

objetivo = normalizar_ticket(TICKET)
if not objetivo:
    fallar(f"El ticket '{TICKET}' no contiene digitos.")

# ---------- Columna destino ----------
listas = llamar("GET", f"/boards/{BOARD}/lists", {"fields": "name"})
destino = next((l for l in listas if l["name"].strip().lower() == COLUMNA.lower()), None)
if not destino:
    nombres = ", ".join(l["name"] for l in listas)
    fallar(f"No existe la columna '{COLUMNA}'. Columnas del tablero: {nombres}")

# ---------- Tarjetas y campos personalizados ----------
tarjetas = llamar("GET", f"/boards/{BOARD}/cards", {
    "fields": "name,shortLink,shortUrl,idList",
    "customFieldItems": "true",
    "filter": "open",
})

campos = llamar("GET", f"/boards/{BOARD}/customFields") or []
definicion = next((c for c in campos if c.get("name", "").strip().lower() == CAMPO.lower()), None)

tarjeta = None
metodo = ""

if definicion:
    tarjeta = buscar_por_campo(tarjetas, definicion["id"], objetivo)
    if tarjeta:
        metodo = f"campo personalizado '{CAMPO}'"

if not tarjeta:
    tarjeta = buscar_por_titulo(tarjetas, objetivo)
    if tarjeta:
        metodo = "patron #NUMERO en el titulo"

if not tarjeta:
    muestra = "; ".join(t.get("name", "")[:50] for t in tarjetas[:8]) or "(ninguna)"
    fallar(
        f"No se encontro ninguna tarjeta con el ticket {objetivo}. "
        f"Verifica el campo '{CAMPO}' o que el titulo incluya #{objetivo}. "
        f"Tarjetas abiertas en el tablero: {muestra}"
    )

origen = next((l["name"] for l in listas if l["id"] == tarjeta["idList"]), "desconocida")

# ---------- Mover y comentar ----------
movida = tarjeta["idList"] != destino["id"]
if movida:
    llamar("PUT", f"/cards/{tarjeta['id']}", {"idList": destino["id"]})

if COMENTARIO:
    llamar("POST", f"/cards/{tarjeta['id']}/actions/comments", {"text": COMENTARIO})

print(f"Ticket {objetivo} -> tarjeta '{tarjeta['name']}'")
print(f"  identificada por: {metodo}")
print(f"  {origen} -> {destino['name']}" if movida else f"  ya estaba en {destino['name']}")

resumen = os.environ.get("GITHUB_STEP_SUMMARY")
if resumen:
    with open(resumen, "a") as s:
        s.write("## Ajuste Trello\n\n| Item | Valor |\n|---|---|\n")
        s.write(f"| Ticket | {objetivo} |\n")
        s.write(f"| Tarjeta | [{tarjeta['name']}]({tarjeta['shortUrl']}) |\n")
        s.write(f"| Identificada por | {metodo} |\n")
        s.write(f"| Columna anterior | {origen} |\n")
        s.write(f"| Columna actual | **{destino['name']}** |\n")
        if COMENTARIO:
            s.write("| Comentario | agregado |\n")
        s.write("\n")