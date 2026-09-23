#!/usr/bin/env python3
"""Valida properties.yml: claves obligatorias y valores permitidos."""
import os
import sys

import yaml

ARCHIVO = "properties.yml"

OBLIGATORIAS = ["Pais", "Owner", "Equipo", "Aplicacion", "Lenguaje", "Criticidad", "Entorno", "Ticket", "TableroTrello"]
PERMITIDOS = {
    "Pais": ["ARGENTINA", "CHILE", "URUGUAY", "PARAGUAY"],
    "Lenguaje": ["PYTHON", "JAVA", "DOTNET"],
    "Criticidad": ["BAJA", "MEDIA", "ALTA"],
    "Entorno": ["DESARROLLO", "TESTING", "PRODUCCION"],
}

errores = []

if not os.path.exists(ARCHIVO):
    print(f"::error::No existe {ARCHIVO} en la raiz del repositorio.")
    sys.exit(1)

with open(ARCHIVO) as f:
    props = yaml.safe_load(f) or {}

for clave in OBLIGATORIAS:
    if clave not in props or props[clave] in (None, ""):
        errores.append(f"Falta la clave obligatoria: {clave}")

ticket = str(props.get("Ticket", "")).strip()
if ticket and not ticket.isdigit():
    errores.append(f"Ticket='{ticket}' debe ser numerico (ej. 507954)")

for clave, valores in PERMITIDOS.items():
    actual = props.get(clave)
    if actual and str(actual).upper() not in valores:
        errores.append(f"{clave}='{actual}' no permitido. Valores validos: {', '.join(valores)}")

# Resumen en la UI de GitHub Actions
resumen = os.environ.get("GITHUB_STEP_SUMMARY")
if resumen:
    with open(resumen, "a") as s:
        s.write("## Check Context\n\n| Clave | Valor |\n|---|---|\n")
        for clave in OBLIGATORIAS:
            s.write(f"| {clave} | {props.get(clave, '(ausente)')} |\n")
        s.write("\n")
        if errores:
            s.write("**Contexto invalido:**\n\n")
            for e in errores:
                s.write(f"- {e}\n")
        else:
            s.write("**Contexto valido.**\n")

# Exponer valores a los jobs siguientes
salida = os.environ.get("GITHUB_OUTPUT")
if salida and not errores:
    with open(salida, "a") as o:
        o.write(f"lenguaje={str(props.get('Lenguaje', '')).upper()}\n")
        o.write(f"owner={props.get('Owner', '')}\n")
        o.write(f"pais={str(props.get('Pais', '')).upper()}\n")
        o.write(f"aplicacion={props.get('Aplicacion', '')}\n")
        o.write(f"criticidad={str(props.get('Criticidad', '')).upper()}\n")
        o.write(f"ticket={props.get('Ticket', '')}\n")
        o.write(f"tablero={props.get('TableroTrello', '')}\n")

for e in errores:
    print(f"::error::{e}")

sys.exit(1 if errores else 0)
