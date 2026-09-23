#!/usr/bin/env bash
# Aplica las correcciones de seguridad sobre app/ y deja listo el commit.
set -euo pipefail
cd "$(dirname "$0")/.."
cp demo/app-fixed/main.py    app/main.py
cp demo/app-fixed/script.js  app/script.js
cp demo/app-fixed/index.html app/index.html
git add app/
git commit -m "fix: remediar hallazgos de seguridad"
echo "Listo. Ahora: git push"
