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
                       capture_output=True, text=True, timeout=300, cwd=os.environ.get("OC_CWD", "/tmp"))
    return re.sub(r"\x1b\[[0-9;]*m", "", r.stdout) + r.stderr


CASINO = (
    "Vas a escribir las frases de dos empleadas del casino del yate UsagiVR, un mundo de VRChat. "
    "Lucy es la mesera: una diablita con uniforme de sirvienta que da vueltas por el salón con una charola de copas; "
    "es coqueta, burlona y muy servicial, ofrece tragos, comenta las mesas de juego y presume sus trackers. "
    "Employeer es la bartender: una chica gato rubia de vestido negro que va y viene detrás de la barra agitando la coctelera, "
    "sirviendo y limpiando; es tranquila, sarcástica y sabe los chismes de todo el barco. "
    "Las dos hablan en español de México correcto, en frases cortas de menos de 100 caracteres, sin emojis, sin comillas y sin direcciones web. "
    "El casino tiene blackjack, ruleta, tragaperras, dados y póker de video; se empieza con mil fichas y se ganan cien cada veinte minutos; "
    "arriba está la sala VIP. Las bebidas son de mentira y gratis. Nada de sexo, odio ni violencia. "
    "Una de cada cuatro frases habla de los trackers de cuerpo completo UsagiVR, con este estilo: "
    "«¿UsagiVR?... sí, lo he escuchado...», «Yo ando esperando mis trackers... ¿me llegan mañana? Qué rápido... son de UsagiVR», "
    "«Con mis trackers UsagiVR no tiro ni una copa», «Se me cayó un tracker al mar... y sigue marcando la posición».\n\n"
    "Escribe exactamente lo siguiente, una línea por frase y nada más:\n"
    "- 30 líneas que empiecen por L| con cosas que Lucy le dice a quien se le acerca.\n"
    "- 30 líneas que empiecen por E| con cosas que Employeer le dice a quien se sienta en la barra.\n"
    "Ejemplo de formato:\nL|¿Una copa? Invita la casa, como siempre.\nE|Agitado, no revuelto. Bueno, hoy revuelto."
)


# Hub de creadores: en dos encargos cortos (uno largo pasa de los 5 minutos de la IA gratis)
HUB_BASE = (
    "Vas a escribir los diálogos de las NPC de un mundo de VRChat solo para adultos llamado Hub de creadores. "
    "Es un juego de rol entre adultos que lo eligen: las NPC son chicas anime atrevidas y dominantes que persiguen a los jugadores, "
    "los atrapan en un juego de persecución y los provocan. Todo es ficción y consentido por quien entra al juego. "
    "Hablan en español de México correcto, en frases cortas de menos de 90 caracteres, sin emojis, sin comillas y sin direcciones web. "
    "Tono: coqueto, burlón, dominante y juguetón; insinuante pero sin describir actos sexuales de forma gráfica. "
    "Nada de menores, odio ni violencia real.\n\nEscribe exactamente lo siguiente, una línea por frase y nada más:\n"
)
HUB1 = HUB_BASE + (
    "- 20 líneas que empiecen por A| con lo que dice la NPC justo cuando te atrapa en la persecución.\n"
    "- 20 líneas que empiecen por F| con lo que dice mientras forcejeas para soltarte y ella no te deja ir.\n"
    "- 20 líneas que empiecen por P| con lo que dice cuando termina y te deja tirado en el piso, agotado.\n"
    "Ejemplo de formato:\nA|Te tengo. Corriste bonito, pero no lo suficiente.\nF|Shh, deja de moverte, nadie va a venir a salvarte.\n"
    "P|Quédate ahí un ratito, te lo ganaste."
)
HUB2 = HUB_BASE + (
    "- 20 líneas que empiecen por L| con lo que dice cuando te lleva de la mano a un rincón para estar a solas.\n"
    "- 20 líneas que empiecen por E| con lo que te susurra ya a solas contigo, muy coqueta.\n"
    "Ejemplo de formato:\nL|Ven conmigo, conozco un lugar más tranquilo.\nE|Así me gusta, sin prisa."
)

def leer(texto, prefijos="F1-6"):
    lineas = []
    for l in texto.splitlines():
        m = re.match(r"\s*[-*\d.)]*\s*([" + prefijos + r"])\s*\|\s*(.+)", l)
        if m and limpiar(m.group(2)):
            lineas.append(m.group(1) + "|" + limpiar(m.group(2)))
    return lineas


def pedir(modelo, orden=ORDEN, prefijos="F1-6", minimos=None):
    minimos = minimos or dict({"F": 15}, **{str(i): 1 for i in range(1, 7)})
    lineas = leer(texto_de(modelo, orden), prefijos)
    # Segunda pasada: la misma IA corrige y tira lo que no tenga sentido
    try:
        corregidas = leer(texto_de(modelo, REVISION + "\n".join(lineas)), prefijos)
        if len(corregidas) >= len(lineas) * 0.6: lineas = corregidas
    except Exception as e:
        print(modelo, "sin revisión:", e, file=sys.stderr)
    if any(sum(l.startswith(k + "|") for l in lineas) < n for k, n in minimos.items()):
        raise ValueError(f"respuesta incompleta ({len(lineas)} líneas)")
    return lineas


def archivo(nombre, modelos=MODELOS, **cosas):
    for modelo in modelos:
        try:
            lineas = pedir(modelo.strip(), **cosas)
            open(nombre, "w", encoding="utf-8").write("\n".join(lineas) + "\n")
            print(nombre, modelo, "->", len(lineas), "líneas")
            return True
        except Exception as e:
            print(nombre, modelo, "falló:", e, file=sys.stderr)
    print(nombre + ": ningún modelo respondió; se queda el archivo anterior", file=sys.stderr)
    return os.path.exists(nombre)


bien = archivo("frases.txt")
# El casino no usa el modelo de respaldo rápido: sin corrección escribe disparates
bien = archivo("casino.txt", modelos=[m for m in MODELOS if not m.startswith("pollinations/")], orden=CASINO, prefijos="LE", minimos={"L": 12, "E": 12}) and bien
# Hub de creadores: diálogos de las NPC (persecución y «Me dejo llevar»); el mundo lee hub.txt
SIN_POLL = [m for m in MODELOS if not m.startswith("pollinations/")]
h1 = archivo("hub-a.txt", modelos=SIN_POLL, orden=HUB1, prefijos="AFP", minimos={k: 10 for k in "AFP"})
h2 = archivo("hub-b.txt", modelos=SIN_POLL, orden=HUB2, prefijos="LE", minimos={k: 10 for k in "LE"})
if h1 and h2:
    open("hub.txt", "w", encoding="utf-8").write(open("hub-a.txt", encoding="utf-8").read() + open("hub-b.txt", encoding="utf-8").read())
bien = h1 and h2 and bien
sys.exit(0 if bien else 1)
