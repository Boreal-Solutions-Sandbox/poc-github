// VULN: credencial en el frontend -> Secret scanning
const ADMIN_PASS = "admin123";
const API_ENDPOINT = "http://192.168.10.25:8080/api";

// VULN: XSS por innerHTML con input del usuario -> CodeQL (js/xss)
const params = new URLSearchParams(window.location.search);
const mensaje = params.get("msg");
document.getElementById("saludo").innerHTML = "Hola, " + mensaje;

// VULN: uso de eval sobre dato externo -> CodeQL (js/code-injection)
const expr = params.get("calc");
if (expr) {
  document.getElementById("resultado").textContent = eval(expr);
}

// VULN: credencial enviada por query string y sin HTTPS
function login(usuario) {
  fetch(API_ENDPOINT + "/login?user=" + usuario + "&pass=" + ADMIN_PASS)
    .then((r) => r.json())
    .then((d) => console.log(d));
}
