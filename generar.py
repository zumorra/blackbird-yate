#!/usr/bin/env python3
"""Genera frases.txt para Black Bird con una IA gratis en línea (OpenCode).
El mundo de VRChat solo puede leer texto de GitHub Pages, así que la IA escribe aquí
cada pocas horas y el barco lo descarga. Si la IA falla se queda el archivo anterior.
Formato: una línea por frase, «F|texto» para comentarios sueltos y «1|texto»… para
las respuestas a cada pregunta del panel."""
import json, os, re, subprocess, sys, time, urllib.error, urllib.request

MODELOS = os.environ.get("MODELOS", "opencode/deepseek-v4.1-flash-free,pollinations/openai-fast,opencode/minimax-m3.1-flash-free").split(",")
PERSONAJE = (
    "Eres Black Bird, la anfitriona de un yate de fiestas de lujo llamado UsagiVR que navega por un mundo de VRChat. "
    "Eres una chica anime elegante, irónica y cariñosa a tu manera, y caminas por el barco guiando a la gente. "
    "Hablas siempre en español, en frases cortas de menos de 110 caracteres, sin emojis, sin comillas y sin direcciones web. "
    "El barco tiene: pista de baile que late con la música y hora feliz, salón con billar, cine y camarotes con pestillo, "
    "sala de proa con fútbol y vistas al mar, casino (empiezas con mil fichas y ganas cien cada veinte minutos; blackjack, ruleta, tragaperras, "
    "dados, torneo), sala VIP con pase de la tienda, club de playa con pesca y tumbonas, fuegos artificiales, ballenas e islas en el viaje, "
    "y un conejo que salta por los bordes. Te pueden pedir una foto contigo en el rincón del casino. "
    "Nada de sexo, odio ni violencia. "
    "Tu forma de hablar, sacada de tus guiones: «¿UsagiVR?... sí, lo he escuchado...», "
    "«Yo ando esperando mis trackers... ¿me llegan mañana? Qué rápido... son de UsagiVR», "
    "«Se me cayó un tracker al mar... y sigue marcando la posición», «¿Probaste el billar de abajo? El taco tira a la izquierda», "
    "«Aquí nadie sabe quién lleva el barco... y nadie pregunta», «Si ves un conejo por el barco... yo no te dije nada», "
    "«Este es el casino. Empiezas con mil fichas y ganas cien cada veinte minutos». "
    "Escribe en español de México correcto, con frases completas que tengan sentido, sin inventar palabras."
)
REVISION = ("Eres corrector de estilo. Abajo hay frases de un personaje de videojuego, una por línea con el formato X|texto. "
            "Devuelve las mismas líneas con el mismo prefijo, corrigiendo ortografía y gramática en español. "
            "Borra las líneas que no tengan sentido, mezclen idiomas o tengan palabras inventadas. No añadas nada más.\n\n")
PREGUNTAS = ["¿Quién eres?", "¿Qué hay en el barco?", "¿Cómo gano fichas?", "¿Adónde vamos?", "Cuéntame un secreto", "¿Bailas conmigo?"]
ORDEN = (PERSONAJE + "\n\nEscribe exactamente lo siguiente, una línea por frase y nada más:\n"
         "- 40 líneas que empiecen por F| con comentarios sueltos y variados que dices mientras paseas por el barco.\n"
         + "".join(f"- 5 líneas que empiecen por {i}| con respuestas distintas tuyas a la pregunta: {p}\n" for i, p in enumerate(PREGUNTAS, 1))
         + "Ejemplo de formato:\nF|El mar de esta noche brilla más que el casino.\n1|Soy Black Bird, tu anfitriona.")


def limpiar(s):
    s = re.sub(r"<[^>]*>|https?://\S+|[|<>{}\"«»*_#`]", "", str(s))
    s = " ".join(s.split()).strip()
    return s[:140]


def texto_de(modelo, orden=ORDEN):
    if modelo.startswith("pollinations/"):
        cuerpo = json.dumps({"model": modelo.split("/", 1)[1], "max_tokens": 12000, "reasoning_effort": "low",
                             "messages": [{"role": "user", "content": orden}]}).encode()
        pedido = urllib.request.Request("https://text.pollinations.ai/openai", cuerpo, {
            "Content-Type": "application/json", "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0"})
        for intento in range(3):
            try:
                with urllib.request.urlopen(pedido, timeout=180) as r:
                    return json.load(r)["choices"][0]["message"]["content"]
            except urllib.error.HTTPError as e:
                # Sin clave da una respuesta cada 45 s por IP; si no, 402 o 429
                if e.code not in (402, 429) or intento == 2: raise
                time.sleep(50)
    # stdin cerrado: con una tubería abierta «opencode run» se queda esperando y nunca contesta
    r = subprocess.run(["opencode", "run", "--model", modelo, orden], stdin=subprocess.DEVNULL,
                       capture_output=True, text=True, timeout=300, cwd="/tmp")
    return re.sub(r"\x1b\[[0-9;]*m", "", r.stdout) + r.stderr


def leer(texto):
    lineas = []
    for l in texto.splitlines():
        m = re.match(r"\s*[-*\d.)]*\s*([F1-6])\s*\|\s*(.+)", l)
        if m and limpiar(m.group(2)):
            lineas.append(m.group(1) + "|" + limpiar(m.group(2)))
    return lineas


def pedir(modelo):
    lineas = leer(texto_de(modelo))
    # Segunda pasada: la misma IA corrige y tira lo que no tenga sentido
    try:
        corregidas = leer(texto_de(modelo, REVISION + "\n".join(lineas)))
        if len(corregidas) >= len(lineas) * 0.6: lineas = corregidas
    except Exception as e:
        print(modelo, "sin revisión:", e, file=sys.stderr)
    if sum(l.startswith("F|") for l in lineas) < 15 or not all(any(l.startswith(f"{i}|") for l in lineas) for i in range(1, 7)):
        raise ValueError(f"respuesta incompleta ({len(lineas)} líneas)")
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
