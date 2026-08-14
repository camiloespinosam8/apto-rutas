# build_incidencias.py — Consolida TODAS las incidencias detectadas leyendo conversaciones
# de Airbnb en un solo incidencias.json, categorizado como pide Camilo:
#   insumos · higiene · tecnico · acceso  (+ otros para lo que no calza)
# Fuentes: barrido 200 hilos (jul), casos de plata (ago), lectura reciente (manual).
# Marca estado abierto/desconocido = NO SOLUCIONADO (el foco).
import csv, json, os, re, sys, unicodedata
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = os.path.dirname(os.path.abspath(__file__))
GO = os.path.join(HERE, "..", "Agente_Guest_Ops")

def norm(s):
    return unicodedata.normalize("NFKD", str(s or "")).encode("ascii", "ignore").decode().lower().strip()

# tipo del barrido -> categoría de Camilo
TIPO2CAT = {
    "falta_amenity": "insumos", "limpieza": "higiene",
    "calefaccion_frio": "tecnico", "wifi_internet": "tecnico", "agua_caliente": "tecnico",
    "electrodomestico": "tecnico", "electricidad": "tecnico", "griferia_agua": "tecnico",
    "acceso_chapa": "acceso", "no_show_reembolso": "otros",
}
# "otro" se desambigua por texto
OTRO_KW = [
    ("fuga de gas", "tecnico"), ("inodoro", "tecnico"), ("tirador", "tecnico"), ("gas", "tecnico"),
    # overbooking / plata primero: "no pudo ingresar" ahí es síntoma, no causa de acceso
    ("no habia disponibilidad", "otros"), ("doble", "otros"), ("reembolso", "otros"),
    ("no pudo ingresar", "acceso"),
]

# CONFIDENCIAL: el panel es público. Nunca publicar montos por cliente (regla de caja/cobros).
RE_PLATA = re.compile(r'\b(?:bruto|neto|total|liquidad\w*|pag\w*)?\s*\$?\s?\d{1,3}(?:[.,]\d{3})+\b', re.I)
def sin_plata(t):
    s = RE_PLATA.sub("[monto reservado]", str(t or ""))
    return re.sub(r'\s{2,}', ' ', s).strip()
ACCION = {
    "insumos": "Checklist de reposición con foto al check-in, cruzado contra lo que promete el anuncio.",
    "higiene": "QA de limpieza con checklist + foto antes de cada check-in (camas, alfombras, baño).",
    "tecnico": "Orden de trabajo a mantención; si se repite en el mismo edificio, tratar como falla de sistema, no de artefacto.",
    "acceso": "Enviar nombres a conserjería 24 h antes del check-in y estandarizar el mensaje de acceso por edificio.",
    "otros": "Resolver caso a caso y dejar la política escrita para que no dependa del criterio del turno.",
}
ACCION_FINA = [
    ("agua_caliente", "Evaluar upgrade de calefón/termo o limitar capacidad máxima; declarar la limitación en el anuncio."),
    ("calefaccion_frio", "Kit de invierno: 1 calefactor por dormitorio + edredón grueso y frazada por cama."),
    ("wifi_internet", "Confirmar internet activo antes del check-in; dejar router y clave documentados en la ficha."),
    ("acceso_chapa", "Enviar nombres a conserjería 24 h antes; crear los accesos que siguen PENDIENTES."),
]

def cat_de(tipo, desc):
    t = norm(tipo)
    if t in TIPO2CAT: return TIPO2CAT[t]
    blob = norm(desc)
    for kw, c in OTRO_KW:
        if kw in blob: return c
    return "otros"

def accion_de(tipo, cat):
    t = norm(tipo)
    for k, a in ACCION_FINA:
        if k == t: return a
    return ACCION.get(cat, ACCION["otros"])

def titulo_de(desc, tipo=""):
    """Titular corto: primera oración útil, sin nombres/fechas/montos de apertura."""
    d = sin_plata(desc)
    if norm(tipo) == "no_show_reembolso":
        return "No se alojó y el reembolso quedó sin resolver"
    s = re.split(r'(?<=[a-zá-úñ])[;.] ', d.strip())[0]
    s = re.sub(r'^[A-ZÁ-Ú][\wá-ú]+ [A-ZÁ-Ú][\wá-ú]+ \([^)]*\)[.:]?\s*', '', s)  # "Nombre Apellido (fechas)."
    s = s.strip().rstrip(".;,")
    return (s[:100] + "…") if len(s) > 102 else s

def limpia_prop(d):
    s = str(d or "").strip()
    s = re.sub(r'\s*\(no en registro\)', ' · sin catastrar', s)
    s = re.sub(r'\s*[—-]\s*T[ÍI]TULO ACTUAL\s*', '', s, flags=re.I)
    s = re.sub(r'listing (\d{6,})', lambda m: "Listing " + m.group(1)[-6:], s)
    return s.strip(" ·-")

ESTADO = {"abierto": "abierto", "resuelto": "resuelto", "desconocido": "sin seguimiento"}
def estado_de(e):
    n = norm(e)
    if n.startswith("abierto"): return "abierto"
    if n.startswith("resuelto"): return "resuelto"
    if "stand by" in n or "espera" in n: return "abierto"
    return "sin seguimiento"

# ---- privacidad: nombres de huéspedes SIEMPRE como "Nombre A." ----
def abrev_nombre(n):
    s = re.sub(r'\s*\(.*$', '', str(n or "")).strip().strip(",")
    if not s: return ""
    if "airbnb" in norm(s) or "servicio al cliente" in norm(s): return "vía Airbnb"
    p = [x for x in s.split() if x]
    if len(p) == 1: return p[0]
    return p[0] + " " + p[1][0].upper() + "."

# Lista real de huéspedes (del índice de reservas) para reemplazarlos también dentro del texto.
# Solo nombres CONOCIDOS: así no se abrevian lugares como "Barrio Italia" o "Mala Yerba".
NOMBRES = []
try:
    _ri = json.load(open(os.path.join(GO, "scripts", "reservas_index.json"), encoding="utf-8"))
    _rr = list(_ri.values()) if isinstance(_ri, dict) else _ri
    for _r in _rr:
        _h = str(_r.get("huesped") or "").strip()
        if len(_h.split()) >= 2: NOMBRES.append(_h)
except Exception as e:
    print("  (no se pudo leer reservas_index:", e, ")")
# Los huespedes historicos ya no estan en el indice de reservas: sumar tambien los nombres
# que traen las propias fuentes de incidencias (columna/campo "huesped").
def _cosechar(nombres):
    for f in ("Incidencias_APTO_2026-07-11.csv", "Incidencias_APTO_2026-08-12.csv"):
        p2 = os.path.join(GO, f)
        if not os.path.exists(p2): continue
        with open(p2, encoding="utf-8-sig", newline="") as fh:
            for row in csv.DictReader(fh):
                for parte in str(row.get("huesped") or "").replace(" y ", ",").split(","):
                    if len(parte.strip().split()) >= 2: nombres.append(parte.strip())
    for f in ("incidencias_manual.json", "incidencias_extra.json", "incidencias_nuevas.json"):
        p2 = os.path.join(HERE, f)
        if not os.path.exists(p2): continue
        for r in json.load(open(p2, encoding="utf-8")):
            h = str(r.get("huesped") or "").strip()
            if len(h.split()) >= 2: nombres.append(h)
_cosechar(NOMBRES)
NOMBRES = sorted({n for n in NOMBRES if "airbnb" not in norm(n)}, key=len, reverse=True)
print(f"  nombres a abreviar: {len(NOMBRES)}")

def sin_apellidos(t):
    s = str(t or "")
    for n in NOMBRES:
        if n in s: s = s.replace(n, abrev_nombre(n))
    return s

def limpia(t):
    """Todo lo que se publica pasa por acá: sin montos por cliente y sin apellidos."""
    return sin_apellidos(sin_plata(t))

out, vistos = [], set()
def add(rec):
    k = (norm(rec["prop"])[:40], norm(rec["titulo"])[:60])
    if k in vistos: return
    vistos.add(k); out.append(rec)

def leer_csv(nombre, fecha):
    p = os.path.join(GO, nombre)
    if not os.path.exists(p):
        print("  (falta", nombre, ")"); return 0
    n = 0
    with open(p, encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            if not row.get("descripcion"): continue
            cat = cat_de(row.get("tipo"), row.get("descripcion"))
            add({
                "cat": cat, "sev": norm(row.get("severidad")) or "media",
                "estado": estado_de(row.get("estado")),
                "prop": limpia_prop(row.get("depto")), "fecha": fecha,
                "huesped": abrev_nombre((row.get("huesped") or "").split(",")[0].split(" y ")[0]),
                "titulo": limpia(titulo_de(row.get("descripcion"), row.get("tipo"))),
                "detalle": limpia(row.get("descripcion")),
                "cita": limpia((row.get("evidencia") or "").strip()[:180]),
                "accion": accion_de(row.get("tipo"), cat),
                "tipo": norm(row.get("tipo")),
            })
            n += 1
    return n

print("Fuentes:")
print("  jul-11 (200 hilos):", leer_csv("Incidencias_APTO_2026-07-11.csv", "2026-07-11"))
print("  ago-12 (plata):    ", leer_csv("Incidencias_APTO_2026-08-12.csv", "2026-08-12"))

def leer_json(nombre, etiqueta):
    p = os.path.join(HERE, nombre)
    if not os.path.exists(p):
        print(f"  {etiqueta}: (falta {nombre})"); return
    n = 0
    for r in json.load(open(p, encoding="utf-8")):
        r.setdefault("estado", "abierto"); r.setdefault("cita", ""); r.setdefault("tipo", r.get("cat"))
        r["detalle"] = limpia(r.get("detalle")); r["titulo"] = limpia(r.get("titulo"))
        r["cita"] = limpia(r.get("cita")); r["huesped"] = abrev_nombre(r.get("huesped"))
        r["prop"] = limpia(r.get("prop"))
        add(r); n += 1
    print(f"  {etiqueta}:", n)

leer_json("incidencias_manual.json", "lectura reciente ")
leer_json("incidencias_extra.json", "barridos previos ")
leer_json("incidencias_nuevas.json", "136 conversaciones")

ORD_S = {"alta": 0, "media": 1, "baja": 2}
ORD_E = {"abierto": 0, "sin seguimiento": 1, "resuelto": 2}
out.sort(key=lambda r: (ORD_E.get(r["estado"], 1), ORD_S.get(r["sev"], 1), r["prop"]))
json.dump(out, open(os.path.join(HERE, "incidencias.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

from collections import Counter
print("\nTOTAL:", len(out))
print("  por categoría:", dict(Counter(r["cat"] for r in out)))
print("  por estado:   ", dict(Counter(r["estado"] for r in out)))
ns = [r for r in out if r["estado"] != "resuelto"]
print(f"  NO SOLUCIONADAS: {len(ns)} ({round(100*len(ns)/max(len(out),1))}%)")
