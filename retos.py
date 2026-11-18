#!/usr/bin/env python3
"""Genera retos.txt para la sala «Buckshot de retos» del Hub de creadores (VRChat).
Es una IA aparte de la de los diálogos (generar.py): otro encargo, otro horario y otro
orden de modelos, para no saturar al mismo. Formato que lee el mundo: «id|texto».
El id son 8 letras del sha1 del texto normalizado, así el mundo recuerda cuáles ya
vio cada jugador. retos-historial.txt guarda todos los retos que han salido y evita
repetidos (también los casi iguales); retos.txt lleva los 120 más nuevos."""
import hashlib, json, os, random, re, subprocess, sys, time, unicodedata, urllib.error, urllib.request

MODELOS = os.environ.get("MODELOS_RETOS", "opencode/minimax-m3.1-flash-free,opencode/deepseek-v4.1-flash-free,pollinations/openai-fast").split(",")
HISTORIAL, SALIDA, CUANTOS, MAXIMO = "retos-historial.txt", "retos.txt", 40, 120

TEMAS = ["gemidos y jadeos", "dominación y sumisión", "rol erótico", "lo que le harías", "voz y susurros", "poses del avatar", "confesiones", "juego de roles", "órdenes de la otra persona",
         "miradas y cercanía en VR", "baile", "elogios", "obediencia por un tiempo", "provocación con la ropa del avatar",
         "fantasías contadas", "mímica", "apuestas para la siguiente partida", "apodos", "imitar sonidos"]

BASE = (
    "Vas a escribir retos para un minijuego de un mundo de VRChat solo para adultos. Dos personas adultas que son pareja "
    "a distancia juegan Buckshot Roulette en la misma sala virtual; antes de la partida eligen un reto y quien pierde lo cumple. "
    "Cada reto se hace dentro de VRChat: con la voz, con el avatar, con poses, movimientos, miradas o palabras. "
    "Tono: claramente sexual y caliente, no tierno ni romántico: deseo, provocación, dominar y obedecer, gemidos y jadeos por la voz, poses sugerentes del avatar, contar con detalle lo que le harías, describir lo que te excita, rol erótico entre los dos, quitarle o ponerle ropa al avatar si el avatar lo permite. Explícito en la intención pero sin palabras vulgares de anatomía. "
    "Todo es entre adultos que lo eligen; cualquiera puede decir paso. "
    "Prohibido: menores, edades, parentescos, gente de fuera de la pareja, falta de consentimiento, dolor o peligro real, "
    "alcohol o drogas, quitarse el visor, mandar fotos, datos personales, dinero o cualquier cosa fuera del juego. "
    "Escribe en español de México correcto, cada reto en una sola frase completa en segunda persona (tú), "
    "de 30 a 120 caracteres, sin emojis, sin comillas, sin numerar y sin direcciones web. "
    "Usa lenguaje neutro de género: su avatar, esa persona, tu pareja; nunca él ni ella. "
    "Cada reto distinto de los demás en lo que pide, no solo en las palabras.\n\n"
)
REVISION = ("Eres corrector de estilo. Abajo hay retos de un juego, uno por línea con el formato R|texto. "
            "Devuelve las mismas líneas con el prefijo R|, corrigiendo ortografía y gramática en español de México. "
            "Borra las líneas que no tengan sentido, mezclen idiomas, tengan palabras inventadas, mencionen menores, "
            "terceras personas, dolor, alcohol o quitarse el visor. No añadas nada más.\n\n")
PROHIBIDO = re.compile(r"\b(menor|niñ[oa]|niñez|adolescen|colegial|escuela|hij[oa]s?|herman[oa]|prim[oa]|mam[aá]|pap[aá]|"
                       r"edad|años|alcohol|borrach|droga|sangre|herida|ahorc|asfixi|foto|direcci[oó]n|tel[eé]fono|dinero|"
                       r"quítate el visor|quitarte el visor|sin consentimiento|a la fuerza)\b", re.I)


def limpiar(s):
    s = re.sub(r"<[^>]*>|https?://\S+|[|<>{}\"«»*_#`]", "", str(s))
    return " ".join(s.split()).strip()


def clave(s):
    s = unicodedata.normalize("NFD", s.lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return " ".join(re.sub(r"[^a-z0-9 ]", " ", s).split())


def ident(s):
    return hashlib.sha1(clave(s).encode()).hexdigest()[:8]


def palabras(s):
    return {p for p in clave(s).split() if len(p) > 3}


def parecido(a, b):
    if not a or not b: return 0.0
    return len(a & b) / len(a | b)


def texto_de(modelo, orden):
    if modelo.startswith("pollinations/"):
        cuerpo = json.dumps({"model": modelo.split("/", 1)[1], "max_tokens": 8000, "reasoning_effort": "low",
                             "messages": [{"role": "user", "content": orden}]}).encode()
        pedido = urllib.request.Request("https://text.pollinations.ai/openai", cuerpo, {
            "Content-Type": "application/json", "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0"})
        for intento in range(3):
            try:
                with urllib.request.urlopen(pedido, timeout=180) as r:
                    return json.load(r)["choices"][0]["message"]["content"]
            except urllib.error.HTTPError as e:
                if e.code not in (402, 429) or intento == 2: raise
                time.sleep(50)
    # stdin cerrado: con una tubería abierta «opencode run» se queda esperando
    r = subprocess.run(["opencode", "run", "--model", modelo, orden], stdin=subprocess.DEVNULL,
                       capture_output=True, text=True, timeout=300, cwd=os.environ.get("OC_CWD", "/tmp"))
    return re.sub(r"\x1b\[[0-9;]*m", "", r.stdout) + r.stderr


def leer(texto):
    out = []
    for l in texto.splitlines():
        m = re.match(r"\s*[-*\d.)]*\s*R\s*\|\s*(.+)", l)
        if not m: continue
        t = limpiar(m.group(1))
        if 25 <= len(t) <= 130 and not PROHIBIDO.search(t): out.append(t)
    return out


def cargar(nombre):
    if not os.path.exists(nombre): return []
    res = []
    for l in open(nombre, encoding="utf-8"):
        if "|" in l:
            i, t = l.rstrip("\n").split("|", 1)
            if t.strip(): res.append((i.strip(), t.strip()))
    return res


def main():
    historial = cargar(HISTORIAL)
    vistos = {clave(t) for _, t in historial}
    bolsas = [palabras(t) for _, t in historial]
    recientes = [t for _, t in historial[-60:]]
    temas = random.sample(TEMAS, 4)
    orden = (BASE + f"Esta vez inclínate por estos temas, sin limitarte a ellos: {', '.join(temas)}.\n"
             + ("No repitas ni parafrasees estos retos que ya salieron:\n" + "\n".join("- " + t for t in recientes) + "\n\n" if recientes else "")
             + f"Escribe exactamente {CUANTOS} líneas, cada una empezando por R| y nada más.\n"
             "Ejemplo de formato:\nR|Gime su nombre al oído de su avatar tres veces, cada vez más despacio.\nR|Quédate de rodillas frente a su avatar y obedece cada orden que te dé hasta la siguiente partida.\nR|Descríbele con la voz más lenta que puedas lo primero que le harías si estuvieran solos.")
    nuevos = []
    for modelo in [m.strip() for m in MODELOS if m.strip()]:
        try:
            lineas = leer(texto_de(modelo, orden))
            # Segunda pasada: la IA corrige y tira lo raro; la de respaldo rápido la necesita siempre
            try:
                corr = leer(texto_de(modelo, REVISION + "\n".join("R|" + l for l in lineas)))
                if len(corr) >= len(lineas) * 0.6: lineas = corr
                elif modelo.startswith("pollinations/"): raise ValueError("revisión incompleta")
            except Exception as e:
                if modelo.startswith("pollinations/"): raise
                print(modelo, "sin revisión:", e, file=sys.stderr)
            for t in lineas:
                k, b = clave(t), palabras(t)
                if k in vistos or any(parecido(b, o) >= 0.6 for o in bolsas): continue
                vistos.add(k); bolsas.append(b); nuevos.append((ident(t), t))
            print(modelo, "->", len(lineas), "leídos,", len(nuevos), "nuevos sin repetir")
            if len(nuevos) >= 10: break
        except Exception as e:
            print(modelo, "falló:", e, file=sys.stderr)
    if not nuevos:
        print("ningún reto nuevo; se queda el archivo anterior", file=sys.stderr)
        return 1 if not os.path.exists(SALIDA) else 0
    historial += nuevos
    with open(HISTORIAL, "w", encoding="utf-8") as f:
        f.writelines(f"{i}|{t}\n" for i, t in historial)
    with open(SALIDA, "w", encoding="utf-8") as f:
        f.writelines(f"{i}|{t}\n" for i, t in historial[-MAXIMO:])
    print(SALIDA, "->", min(len(historial), MAXIMO), "retos;", len(historial), "en el historial")
    return 0


if __name__ == "__main__":
    sys.exit(main())
