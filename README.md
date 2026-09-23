# POC GitHub

Demostración de GitHub como plataforma de CI/CD y control de cambios.
Sin herramientas pagas: todo corre con Actions, Semgrep OSS y Trivy.

> La aplicación de `app/` tiene **vulnerabilidades sembradas a propósito**.

---

## Arquitectura

```
.github/workflows/
  base.yml     Workflow REUTILIZABLE. No se dispara solo.
               STEP 1  Check Context   -> valida properties.yml
               STEP 2  Security Scan   -> Semgrep + Trivy

  ci.yml       Se dispara en push a cualquier rama (menos main) y en cada PR.
               Llama a base.yml. NO despliega.

  deploy.yml   Se dispara cuando alguien APRUEBA un Pull Request.
               1. Verifica que el aprobador este autorizado
               2. Vuelve a llamar a base.yml sobre el codigo del PR
               3. Deploy (simulado), con aprobacion de environment
```

La lógica de contexto y seguridad está escrita **una sola vez**, en `base.yml`.
Los otros dos workflows la invocan con `uses:`. Si mañana se agrega un escáner,
se agrega en un solo lugar.

---

## STEP 1 — Check Context

Lee `properties.yml` de la raíz del repo:

```yaml
Pais: ARGENTINA
Owner: Ramiro
Equipo: devs
Aplicacion: demo-poc
Lenguaje: PYTHON
Criticidad: MEDIA
Entorno: DESARROLLO
```

`scripts/check_context.py` valida dos cosas:

- **Claves obligatorias presentes**: las siete de arriba
- **Valores dentro de lo permitido**: Lenguaje solo `PYTHON|JAVA|DOTNET`,
  Pais solo `ARGENTINA|CHILE|URUGUAY|PARAGUAY`, etc.

Si falla, el pipeline corta ahí y el escaneo ni se ejecuta.
Los valores se exportan como outputs para los jobs siguientes.

**Para cambiar las reglas**, editá las listas `OBLIGATORIAS` y `PERMITIDOS`
al principio de `scripts/check_context.py`.

---

## STEP 2 — Security Scan

Dos herramientas, ambas gratuitas y sin cuenta:

| Herramienta | Qué cubre |
|---|---|
| **Semgrep OSS** | SAST: SQL injection, XSS, eval, credenciales hardcodeadas |
| **Trivy** | Dependencias vulnerables, secretos, misconfiguraciones |

Semgrep corre con **reglas locales** (`.semgrep/rules.yml`) más el ruleset
público `p/security-audit`. Las locales garantizan hallazgos aunque el registry
externo no esté disponible.

**Resultado verificado sobre `app/`: 10 hallazgos.**

| Severidad | Regla | Ubicación |
|---|---|---|
| ERROR | credencial-hardcodeada-py | `app/main.py:8` |
| ERROR | credencial-hardcodeada-py | `app/main.py:9` |
| WARNING | url-insegura-py | `app/main.py:12` |
| ERROR | sql-injection | `app/main.py:26` |
| ERROR | flask-debug | `app/main.py:38` |
| WARNING | bind-todas-las-interfaces | `app/main.py:38` |
| ERROR | credencial-hardcodeada-js | `app/script.js:2` |
| WARNING | url-insegura-js | `app/script.js:3` |
| ERROR | xss-innerhtml | `app/script.js:8` |
| ERROR | eval | `app/script.js:13` |

Con la versión corregida (`demo/app-fixed/`): **0 hallazgos**.

---

## Deploy tras aprobación

`deploy.yml` usa el evento `pull_request_review`. Cuando alguien aprueba un PR:

**1. Verificación del aprobador.** El evento se dispara con *cualquier*
aprobación, así que el workflow valida explícitamente:

- `author_association` debe ser `OWNER`, `MEMBER` o `COLLABORATOR`
- el autor del PR no puede autoaprobarse

**2. Revalidación.** Vuelve a correr `base.yml`, pero apuntando al commit
del PR (`head.sha`), no a `main`. Importa: sin esto escanearía el código
equivocado.

**3. Deploy.** Job con `environment: produccion`, lo que agrega una **segunda**
aprobación — la del environment, configurada en la UI. Es simulado: imprime
los metadatos y unos pasos de ejemplo. No toca infraestructura.

Dos controles independientes: quién aprueba el código (PR) y quién autoriza
el despliegue (environment).

---

## Setup

### 1. Subir el repo

```bash
git add .
git commit -m "Pipeline base"
git push
```

El token necesita scopes `repo` **y** `workflow`.

### 2. Environment

`Settings > Environments > New environment` → `produccion`

- Tildar **Required reviewers** y agregar al aprobador

### 3. Ruleset sobre main

`Settings > Rules > New ruleset` → target `main`

- Require a pull request before merging (1 approval)
- Require review from Code Owners
- Require status checks: `Contexto y seguridad / Check Context`,
  `Contexto y seguridad / Security Scan`
- Block force pushes

> Los nombres de los checks reutilizados llevan el prefijo del job que los
> llama. Aparecen en el buscador después de la primera corrida.

### 4. Teams

En la org: crear `devs` y `seguridad`, darles acceso **Write** al repo.
Sin eso, CODEOWNERS no funciona.

---

## Guion de la demo

### Acto 1 — El pipeline base falla (10 min)

```bash
git checkout -b feature/nueva-pantalla
# tocar cualquier cosa en app/
git commit -am "cambio" && git push -u origin feature/nueva-pantalla
```

Mostrar en Actions: `Check Context` en verde con la tabla de metadatos,
`Security Scan` en rojo con los 10 hallazgos en el Step Summary.

### Acto 2 — Contexto inválido (5 min)

```bash
cp demo/properties-invalido.yml properties.yml
git commit -am "cambiar metadatos" && git push
```

`Check Context` falla: `Pais='BRASIL' no permitido`, `Lenguaje='GOLANG' no
permitido`. **El escaneo ni siquiera arranca** — el gate de contexto corta antes.

Revertir: `git checkout HEAD~1 properties.yml`

### Acto 3 — PR bloqueado (10 min)

Abrir el PR contra `main`. Mostrar los checks en rojo y el merge deshabilitado
por el ruleset. Mostrar CODEOWNERS pidiendo revisión del equipo de seguridad.

### Acto 4 — Corregir, aprobar, desplegar (15 min)

```bash
./scripts/aplicar-fix.sh
git push
```

Checks en verde. El aprobador entra al PR y hace **Approve**.

Ahí se dispara `deploy.yml`: verifica el aprobador, revalida contexto y
seguridad, y el job de deploy queda **esperando la aprobación del environment**.
Confirmar y mostrar el registro.

Si intentás aprobar tu propio PR, el workflow falla con
`El autor del PR no puede autoaprobar su propio cambio`.

---

## Contenido

```
.github/workflows/base.yml       Check Context + Security Scan (reutilizable)
.github/workflows/ci.yml         Disparo en push y PR
.github/workflows/deploy.yml     Disparo por aprobacion de PR + deploy
.github/dependabot.yml           Actualizacion de dependencias
.github/CODEOWNERS               Revision obligatoria por equipo
.semgrep/rules.yml               9 reglas locales de seguridad
properties.yml                   Metadatos validados por Check Context
scripts/check_context.py         Validador de properties.yml
scripts/aplicar-fix.sh           Aplica las correcciones (Acto 4)
app/                             Aplicacion vulnerable
demo/app-fixed/                  Version corregida
demo/properties-invalido.yml     Para demostrar el fallo de contexto
```

---

## Notas

- **CodeQL quedó afuera** a propósito. Es gratis en repos públicos, pero en
  repos privados requiere licencia de seguridad. Semgrep y Trivy son gratuitos
  en cualquier caso.
- **Trivy tiene `exit-code: '0'`**: reporta pero no bloquea. El corte lo hace
  Semgrep. Si querés que Trivy también bloquee, cambiá a `exit-code: '1'`.
- **Licenciamiento**: verificá precios actuales antes de presentar. GitHub
  reorganizó los SKUs de seguridad y esta información puede estar desactualizada.
