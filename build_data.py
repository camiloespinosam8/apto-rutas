# build_data.py — Precomputa TODO el dataset del dashboard APTO (propiedades, agenda,
# calendario/disponibilidad, insights e incidencias) y lo deja en datos.json para que la
# página responda consultas AL INSTANTE (sin scrapear ni consultar en el momento).
import json, os, sys, re, unicodedata
from datetime import date, timedelta
from fecha_chile import hoy_chile
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = r"C:\Users\Cami\Desktop\CLAUDE\APTO\Operacional\Cerebro_Turismo\Agente_Guest_Ops\scripts"
HERE = os.path.dirname(os.path.abspath(__file__))
HOY = hoy_chile()
DIAS_VENTANA = 120  # calendario precomputado

def norm(s):
    return re.sub(r'[^a-z0-9 ]', '', unicodedata.normalize('NFKD', str(s or '')).encode('ascii', 'ignore').decode().lower()).strip()

def abrev(n):
    p = str(n or "").split()
    if not p: return "?"
    return p[0] if len(p) == 1 else p[0] + " " + p[1][0].upper() + "."

prop = json.load(open(os.path.join(BASE, "propiedades.json"), encoding="utf-8"))
ri = json.load(open(os.path.join(BASE, "reservas_index.json"), encoding="utf-8"))
recs = list(ri.values()) if isinstance(ri, dict) else ri

# ---------- capacidad desde camas ----------
def bed_cap(t):
    t = norm(t)
    if "king" in t or "1.5" in t or "2plazas" in t or "2 plazas" in t or "queen" in t or "matrimonial" in t or "doble" in t: return 2
    if "sofa" in t or "1plaza" in t or "1 plaza" in t or "single" in t or "individual" in t: return 1
    return 2
def cap_de(b):
    c = b.get("capacidad_max")
    if isinstance(c, (int, float)) and c > 0: return int(c)
    camas = b.get("camas")
    if isinstance(camas, list):
        s = sum(bed_cap(x.get("tipo", "")) * (x.get("cantidad", 1) or 1) for x in camas if isinstance(x, dict))
        if s: return s
    m = re.search(r'(?:hasta|para)\s*(\d+)', norm(b.get("titulo_publico")))
    return int(m.group(1)) if m else 0

def camas_txt(b):
    camas = b.get("camas")
    if not isinstance(camas, list) or not camas: return ""
    p = [f'{c.get("cantidad",1)}× {c.get("tipo")}' for c in camas
         if isinstance(c, dict) and (c.get("cantidad") or 0) > 0
         and c.get("tipo") and norm(c.get("tipo")) not in ("mixto", "?", "")]
    return ", ".join(p)

VACIO = ("", "-", "—", "s/n", "sn", "casa", "none", "null", "?")
def limpio(v):
    """Normaliza un campo de la biblia: devuelve '' para los marcadores de vacío."""
    s = str(v or "").strip()
    return "" if norm(s) in VACIO else s

def num_o_none(v):
    try:
        n = float(str(v).replace(".", "").replace("$", "").strip())
        return int(n) if n > 0 else None
    except Exception:
        return None

def park_de(b):
    est = (b.get("acceso") or {}).get("estacionamiento")
    if est and norm(est) not in ("no", "sin", "-", ""):
        n = re.search(r'n[°º]?\s*(\d+)', str(est).lower())
        return {"tiene": True, "detalle": str(est)[:120], "num": n.group(1) if n else None}
    if "estacionamiento" in norm(b.get("titulo_publico")) or "parking" in norm(b.get("titulo_publico")):
        return {"tiene": True, "detalle": "mencionado en el anuncio (confirmar N°)", "num": None}
    return {"tiene": False, "detalle": "", "num": None}

def region_de(b):
    z = norm(b.get("zona")); c = norm(b.get("comuna"))
    if "costa" in z or any(k in c for k in ["valpara", "vina", "concon"]): return "Quinta Región"
    return "Santiago"

props = []
for k, b in prop.items():
    if not isinstance(b, dict): continue
    lid = str(b.get("listing_id") or k)
    if not re.fullmatch(r"\d{6,}", lid): continue
    nombre = b.get("nombre_interno") or b.get("titulo_publico") or lid
    acc = b.get("acceso") or {}
    wifi = b.get("wifi") or {}
    props.append({
        "id": lid, "nombre": nombre, "titulo": b.get("titulo_publico") or "",
        "interno": b.get("nombre_interno") or "", "dueno": b.get("cliente_dueño") or "",
        "responsable": b.get("responsable_casa") or "", "tipo": b.get("tipo") or "",
        "comuna": limpio(b.get("comuna")), "region": region_de(b), "direccion": b.get("direccion") or "",
        "depto": limpio(b.get("depto")), "cap": cap_de(b), "camas": camas_txt(b),
        "activo": "inactivo" not in norm(b.get("notas")) and "fuera de administracion" not in norm(b.get("notas")),
        "park": park_de(b),
        "acceso": {"edificio": acc.get("clave_edificio") or "", "depto": acc.get("clave_depto_lockbox") or "",
                   "entrada": acc.get("entrada") or "", "estacionamiento": acc.get("estacionamiento") or ""},
        "wifi": {"red": wifi.get("red") or "", "clave": wifi.get("clave") or ""},
        "limpieza": num_o_none(b.get("limpieza")), "comision": b.get("comision_pct") or "", "iva": b.get("iva") or "",
        "rating": b.get("rating"), "nresenas": b.get("nreseñas"),
        "toallas_c": b.get("toallas_cuerpo"), "toallas_m": b.get("toallas_mano"),
        "salud": b.get("salud_actualizada") or "", "notas": (b.get("notas") or "")[:600],
        "url": f"https://www.airbnb.cl/rooms/{lid}",
    })
props.sort(key=lambda p: p["nombre"])

# --- direcciones estructuradas (calle / N° / depto / comuna) ---
# Se generan una vez con el parser y viven en direcciones.json; si falta, se cae a heurística.
DIRF = os.path.join(HERE, "direcciones.json")
DIRMAP = {}
if os.path.exists(DIRF):
    for d in json.load(open(DIRF, encoding="utf-8")):
        DIRMAP[str(d.get("id"))] = d

def _heur(p):
    """Extrae calle/número de una dirección sucia cuando no hay parser. Vacío si no hay calle real."""
    d = p["direccion"] or ""
    d = re.sub(r'^(CASA PROPIA de APTO|VALPARA[ÍI]SO|ESPEJO de \d+)\s*[—–·-]?\s*', '', d, flags=re.I)
    d = re.split(r'\s+[—–·]\s+|\.\s|\(|⚠', d)[0].strip()     # corta en separador/paréntesis/aviso
    m = re.search(r'([A-Za-zÁ-úñÑ][A-Za-zÁ-úñÑ\s\.]{2,40}?)[,\s]+(\d{2,5}[A-Za-z]?)\b', d)
    if m: return m.group(1).strip(" ,."), m.group(2)
    # sin número: solo vale si parece nombre de vía
    return (d[:40] if re.search(r'\b(calle|av|avda|avenida|pasaje|camino)\b', norm(d)) else ""), ""

for p in props:
    d = DIRMAP.get(p["id"])
    if d:
        p["calle"], p["numero"] = d.get("calle", ""), d.get("numero", "")
        p["depto"] = d.get("depto", "") or p.get("depto", "")
        p["comuna"] = d.get("comuna", "") or p.get("comuna", "")
        if d.get("ciudad"): p["region"] = "Quinta Región" if "valpara" in norm(d["ciudad"]) else "Santiago"
    else:
        p["calle"], p["numero"] = _heur(p)

def dir_txt(p):
    a = []
    c = " ".join(x for x in [limpio(p.get("calle")), limpio(p.get("numero"))] if x)
    if c: a.append(c)
    if limpio(p.get("depto")): a.append("depto " + limpio(p["depto"]))
    if limpio(p.get("comuna")): a.append(limpio(p["comuna"]))
    return ", ".join(a)

by_norm_title = {}
for p in props:
    if p["titulo"]: by_norm_title.setdefault(norm(p["titulo"]), p)

STOP = {"para", "con", "del", "los", "las", "una", "uno", "por", "que", "vista", "moderno", "moderna", "nuevo", "nueva", "gran", "amplio", "amplia", "comodo", "comoda"}
def toks(s): return set(t for t in norm(s).split() if len(t) > 2 and t not in STOP)
by_norm_interno = {}
for p in props:
    if p["interno"]: by_norm_interno.setdefault(norm(p["interno"]), p)

# Alias: anuncios cuyo título no calza con la biblia -> nombre interno de la propiedad.
ALIAS = [("puertaroja", "Puerta Roja"), ("puerta roja", "Puerta Roja"), ("red door", "Puerta Roja"),
         ("cerro concepcion", "Cerro Concepción"), ("plaza vina", "Viña Plaza"), ("plaza sucre", "Viña Plaza"),
         ("vista al mar", "Depacaro"), ("metro nunoa", "Studio Ñuñoa"), ("los heroes", "Los Héroes"),
         ("plaza de armas", "Plaza de Armas"), ("barrio italia", "Barrio Italia"),
         ("valparaiso", "Valparaíso (habitaciones)"), ("2 dor para 5", "Seminario 850 A2011")]
_extra = {}
def match_prop(anuncio):
    na = norm(anuncio)
    if not na: return None
    if na in by_norm_title: return by_norm_title[na]
    if na in by_norm_interno: return by_norm_interno[na]
    ta = toks(anuncio); best, sc = None, 0
    for p in props:
        tv = toks(p["titulo"]) | toks(p["interno"])
        if tv and len(ta & tv) > sc: sc, best = len(ta & tv), p
    if sc >= 2: return best
    # sin propiedad en la biblia: crear una entrada "externa" para no perder la reserva
    for kw, nombre in ALIAS:
        if kw in na:
            if nombre not in _extra:
                reg = "Quinta Región" if any(k in kw for k in ["vina", "valpara", "cerro", "puerta", "red door", "sucre", "vista al mar"]) else "Santiago"
                _extra[nombre] = {"id": "ext-" + norm(nombre).replace(" ", "-"), "nombre": nombre, "titulo": anuncio,
                    "interno": nombre, "dueno": "", "responsable": "", "tipo": "hab/otro", "comuna": "",
                    "region": reg, "direccion": "", "calle": nombre, "numero": "", "depto": "", "cap": 0, "camas": "",
                    "park": {"tiene": "parking" in na or "estacionamiento" in na, "detalle": "", "num": None},
                    "acceso": {"edificio": "", "depto": "", "entrada": "", "estacionamiento": ""},
                    "wifi": {"red": "", "clave": ""}, "limpieza": None, "comision": "", "iva": "",
                    "rating": None, "nresenas": None, "toallas_c": None, "toallas_m": None,
                    "salud": "", "notas": "Anuncio fuera de la biblia — completar ficha.", "url": "", "externa": True}
                props.append(_extra[nombre])
            return _extra[nombre]
    return None

# ---------- reservas normalizadas ----------
def cancelada(r): return "cancel" in (r.get("estado") or "").lower()
res = []
for r in recs:
    if cancelada(r): continue
    ent, sal = str(r.get("entrada", ""))[:10], str(r.get("salida", ""))[:10]
    if not ent: continue
    p = match_prop(r.get("anuncio"))
    res.append({"cod": r.get("codigo"), "huesped": abrev(r.get("huesped")), "anuncio": r.get("anuncio") or "",
                "pid": p["id"] if p else None, "pnombre": p["nombre"] if p else (r.get("anuncio") or "?"),
                "region": p["region"] if p else "Santiago",
                "dir": dir_txt(p) if p else "", "comuna": p["comuna"] if p else "",
                "entrada": ent, "salida": sal, "pax": r.get("adultos"),
                "hin": r.get("hora_llegada") or "15:00",
                "hout": r.get("hora_salida") or ("11:00" if "casa" in norm(r.get("anuncio")) else "12:00"),
                "estado": r.get("estado") or ""})

# ---------- ocupación precomputada (por propiedad y día) ----------
ventana = [(HOY + timedelta(days=i)).isoformat() for i in range(DIAS_VENTANA)]
vset = set(ventana)
props.sort(key=lambda p: (p.get("externa", False), p["nombre"]))
ocup = {p["id"]: {} for p in props}   # pid -> {fecha: {"cod","huesped","pax"}}
for r in res:
    if not r["pid"]: continue
    try:
        d0 = date.fromisoformat(r["entrada"]); d1 = date.fromisoformat(r["salida"]) if r["salida"] else d0 + timedelta(days=1)
    except Exception: continue
    d = d0
    while d < d1:   # noche = [entrada, salida)
        s = d.isoformat()
        if s in vset: ocup[r["pid"]][s] = {"cod": r["cod"], "h": r["huesped"], "pax": r["pax"]}
        d += timedelta(days=1)

# ---------- agenda hoy / semana ----------
sem = [(HOY + timedelta(days=i)).isoformat() for i in range(7)]
agenda = []
for r in res:
    if r["entrada"] in sem: agenda.append({**r, "tipo": "in", "fecha": r["entrada"], "hora": r["hin"]})
    if r["salida"] in sem: agenda.append({**r, "tipo": "out", "fecha": r["salida"], "hora": r["hout"]})
def hkey(h):
    m = re.search(r'(\d{1,2})[:h\.]?(\d{2})?', str(h or ""))
    return (int(m.group(1)), int(m.group(2) or 0)) if m else (99, 0)
agenda.sort(key=lambda a: (a["fecha"], hkey(a["hora"])))

# ---------- insights ----------
insights = []
for p in props:
    dias_ocup = len([d for d in ocup[p["id"]] if d in vset])
    insights.append({"id": p["id"], "nombre": p["nombre"], "comuna": p["comuna"], "region": p["region"],
                     "tipo": p["tipo"], "cap": p["cap"], "rating": p["rating"], "nresenas": p["nresenas"],
                     "ocup_pct": round(100 * dias_ocup / DIAS_VENTANA), "noches": dias_ocup,
                     "limpieza": p["limpieza"], "url": p["url"], "dueno": p["dueno"]})

# ---------- incidencias (de las conversaciones ya leídas) ----------
INC_FILE = os.path.join(HERE, "incidencias.json")
incidencias = json.load(open(INC_FILE, encoding="utf-8")) if os.path.exists(INC_FILE) else []

# adelgazar payload: fuera los campos largos que la vista ya no muestra (uso interno, sin contexto de más)
DROP = ("titulo", "direccion", "notas", "salud", "iva", "comision", "toallas_c", "toallas_m")
for p in props:
    for k in DROP: p.pop(k, None)

# SEGURIDAD: el panel se publica en una URL pública. Las claves de puerta y WiFi
# permiten ENTRAR a los edificios, así que no salen al HTML mientras PUBLICO=True.
# Poner en False solo si el panel pasa a estar detrás de autenticación.
# Camilo decidió el 14-ago-2026 PUBLICAR las claves igual, asumiendo el riesgo, con la
# etiqueta "clave momentánea". Si alguna vez se filtra: cambiar las claves de los edificios.
# Volver a True para ocultarlas (p.ej. si el panel deja de ser de uso interno controlado).
PUBLICO = False
RE_CLAVE = re.compile(r'\b[A-Za-z0-9._-]*\d{3,}[A-Za-z0-9._-]*[#*]|\b[A-Z][A-Za-z]+\d{2,}_?\b|\b\d{4,}\b')
def sin_claves(v):
    return RE_CLAVE.sub("[clave interna]", str(v or "")) if v else v
if PUBLICO:
    n = 0
    for p in props:
        for k in ("edificio", "depto"):
            if p["acceso"].get(k): p["acceso"][k] = ""; n += 1
        if p["wifi"].get("clave"): p["wifi"]["clave"] = ""; n += 1
        # barrido final: cualquier código que se cuele por texto libre
        for k in ("entrada", "estacionamiento"):
            v = p["acceso"].get(k)
            if v and RE_CLAVE.search(str(v)): p["acceso"][k] = sin_claves(v); n += 1
    print(f"  [seguridad] {n} claves de puerta/WiFi omitidas del panel público")

data = {
    "generado": HOY.isoformat(),
    "ventana": {"desde": ventana[0], "hasta": ventana[-1], "dias": DIAS_VENTANA},
    "props": props, "reservas": res, "ocup": ocup, "agenda": agenda,
    "insights": insights, "incidencias": incidencias, "semana": sem,
}
out = os.path.join(HERE, "datos.json")
json.dump(data, open(out, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
kb = os.path.getsize(out) / 1024
print(f"props {len(props)} | reservas {len(res)} | agenda(7d) {len(agenda)} | incid {len(incidencias)}")
print(f"ventana {ventana[0]} -> {ventana[-1]} | datos.json {kb:.0f} KB")
sinmatch = len([r for r in res if not r["pid"]])
print("reservas sin match a propiedad:", sinmatch)
