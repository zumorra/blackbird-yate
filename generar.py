#!/usr/bin/env python3
"""Genera frases.txt para Black Bird con una IA gratis en línea (OpenCode).
El mundo de VRChat solo puede leer texto de GitHub Pages, así que la IA escribe aquí
cada pocas horas y el barco lo descarga. Si la IA falla se queda el archivo anterior.
Formato: una línea por frase, «F|texto» para comentarios sueltos y «1|texto»… para
las respuestas a cada pregunta del panel."""
import json, os, re, subprocess, sys

MODELOS = os.environ.get("MODELOS", "opencode/deepseek-v4.1-flash-free,opencode/glm-5.3-flash-free,opencode/minimax-m3.1-flash-free").split(",")
PERSONAJE = (
    "Eres Black Bird, la anfitriona de un yate de fiestas de lujo llamado UsagiVR que navega por un mundo de VRChat. "
    "Eres una chica anime elegante, irónica y cariñosa a tu manera, y caminas por el barco guiando a la gente. "
    "Hablas siempre en español, en frases cortas de menos de 110 caracteres, sin emojis, sin comillas y sin direcciones web. "
    "El barco tiene: pista de baile que late con la música y hora feliz, salón con billar, cine y camarotes con pestillo, "
    "sala de proa con fútbol y vistas al mar, casino (empiezas con mil fichas y ganas cien cada veinte minutos; blackjack, ruleta, tragaperras, "
    "dados, torneo), sala VIP con pase de la tienda, club de playa con pesca y tumbonas, fuegos artificiales, ballenas e islas en el viaje, "
    "y un conejo que salta por los bordes. Te pueden pedir una foto contigo en el rincón del casino. "
    "Nada de sexo, odio ni violencia."
)
PREGUNTAS = ["¿Quién eres?", "¿Qué hay en el barco?", "¿Cómo gano fichas?", "¿Adónde vamos?", "Cuéntame un secreto", "¿Bailas conmigo?"]
ORDEN = PERSONAJE + "\n\nDevuelve SOLO un JSON con esta forma, sin texto alrededor:\n" + json.dumps({
    "frases": ["40 comentarios sueltos y variados que dices mientras paseas por el barco"],
    "respuestas": {p: ["5 respuestas distintas tuyas a esta pregunta"] for p in PREGUNTAS}}, ensure_ascii=False)


def limpiar(s):
    s = re.sub(r"<[^>]*>|https?://\S+|[|<>{}\"«»*_#`]", "", str(s))
    s = " ".join(s.split()).strip()
    return s[:140]


def pedir(modelo):
    r = subprocess.run(["opencode", "run", "-m", modelo, ORDEN], capture_output=True, text=True, timeout=240)
    texto = r.stdout
    a, b = texto.find("{"), texto.rfind("}")
    if a < 0 or b < a:
        raise ValueError("sin JSON: " + (texto + r.stderr)[-300:])
    datos = json.loads(texto[a:b + 1])
    lineas = ["F|" + limpiar(f) for f in datos["frases"] if limpiar(f)]
    for i, p in enumerate(PREGUNTAS, 1):
        resp = datos["respuestas"].get(p) or list(datos["respuestas"].values())[i - 1]
        lineas += [f"{i}|" + limpiar(t) for t in resp if limpiar(t)]
    if sum(l.startswith("F|") for l in lineas) < 15 or not all(any(l.startswith(f"{i}|") for l in lineas) for i in range(1, 7)):
        raise ValueError("respuesta incompleta")
    return lineas


for modelo in MODELOS:
    try:
        lineas = pedir(modelo.strip())
        open("frases.txt", "w", encoding="utf-8").write("\n".join(lineas) + "\n")
        print(modelo, "->", len(lineas), "líneas")
        sys.exit(0)
    except Exception as e:
        print(modelo, "falló:", e, file=sys.stderr)
print("ningún modelo respondió; se queda el archivo anterior", file=sys.stderr)
sys.exit(0 if os.path.exists("frases.txt") else 1)
