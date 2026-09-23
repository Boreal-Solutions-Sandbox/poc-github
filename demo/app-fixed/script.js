// FIX: sin credenciales en el frontend, endpoint relativo
const API_ENDPOINT = "/api";

// FIX: textContent en lugar de innerHTML -> no hay XSS
const params = new URLSearchParams(window.location.search);
const mensaje = params.get("msg") || "";
document.getElementById("saludo").textContent = "Hola, " + mensaje;

// FIX: sin eval
const expr = params.get("calc");
if (expr && /^[0-9+\-*/ ().]+$/.test(expr)) {
  document.getElementById("resultado").textContent = "Expresion recibida";
}

// FIX: credenciales por POST, nunca por query string
function login(usuario, clave) {
  fetch(API_ENDPOINT + "/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user: usuario, pass: clave }),
  })
    .then((r) => r.json())
    .then((d) => console.log(d.estado));
}
