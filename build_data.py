# build_data.py — Precomputa TODO el dataset del dashboard APTO (propiedades, agenda,
# calendario/disponibilidad, insights e incidencias) y lo deja en datos.json para que la
# página responda consultas AL INSTANTE (sin scrapear ni consultar en el momento).
import json, os, re, sys, unicodedata
from datetime import date, timedelta
from fecha_chile import hoy_chile
import unidades as UN
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

# Región deducida del texto del anuncio, para las que no están en la biblia.
def _region_txt(na):
    return "Quinta Región" if any(k in na for k in
        ["vina", "valpara", "concon", "cerro concepcion", "puerta roja", "puertaroja",
         "red door", "plaza sucre", "sucre", "vista al mar"]) else "Santiago"

_extra = {}
def match_prop(anuncio):
    """SOLO match exacto de título (o de nombre interno).

    El match difuso por palabras fusionaba propiedades DISTINTAS: 'Home studio ...
    Metro' (Pedro de Valdivia 150) y 'Nuevo 2 Dor ... Metro' (Seminario 850) compartían
    'estacionamiento'+'metro' y quedaban como una sola unidad → 84 solapes falsos,
    ocupación inflada y disponibilidad equivocada.

    Ahora, si el anuncio no calza exacto, es su PROPIA unidad. Partir de más es
    inofensivo (se ve una fila extra); fusionar de más corrompe todo el calendario."""
    na = norm(anuncio)
    if not na: return None
    if na in by_norm_title: return by_norm_title[na]
    if na in by_norm_interno: return by_norm_interno[na]
    if na not in _extra:
        _extra[na] = {"id": "ext-" + na.replace(" ", "-")[:40], "nombre": (anuncio or "?")[:60],
            "titulo": anuncio or "", "interno": "", "dueno": "", "responsable": "",
            "tipo": "casa" if "casa" in na else ("hab" if "habitacion" in na or "cama en" in na else ""),
            "comuna": "", "region": _region_txt(na), "direccion": "", "calle": "", "numero": "",
            "depto": "", "cap": 0, "camas": "", "activo": True,
            "park": {"tiene": ("parking" in na or "estacionamiento" in na), "detalle": "", "num": None},
            "acceso": {"edificio": "", "depto": "", "entrada": "", "estacionamiento": ""},
            "wifi": {"red": "", "clave": ""}, "limpieza": None, "comision": "", "iva": "",
            "rating": None, "nresenas": None, "salud": "",
            "notas": "Anuncio sin ficha en la biblia — completar.", "url": "", "externa": True}
        props.append(_extra[na])
    return _extra[na]

# ---------- reservas normalizadas ----------
def cancelada(r): return "cancel" in (r.get("estado") or "").lower()

# ---- reservas FANTASMA -------------------------------------------------------
# reservas_index es append-only: guarda el estado del ÚLTIMO avistamiento y nunca lo
# borra. Cuando una reserva se cancela desaparece del panel de Airbnb, pero su registro
# queda congelado en "Confirmada" para siempre. Sin este filtro esas canceladas siguen
# bloqueando el calendario y chocan con la reserva que tomó su lugar: eso producía
# "sobreventas" que no existen (Antúnez 402, Carol Urzúa 806, Seminario 1001).
# Una reserva YA TERMINADA deja de aparecer por su cuenta: a esas no se les aplica.
_H = HOY.isoformat()
_v = [str(r.get("visto") or "")[:10] for r in recs if r.get("visto")]
ULTIMO_BARRIDO = max([x for x in _v if x <= _H] or [_H])

def fantasma(r):
    sal = str(r.get("salida") or "")[:10]
    if sal and sal < _H: return False          # ya se fue: normal que no la muestre
    v = str(r.get("visto") or "")[:10]
    return bool(v) and v < ULTIMO_BARRIDO


# Una SOLICITUD todavía no ocupa nada: si la cuento como ocupada, el panel muestra
# menos disponibilidad de la real. Solo bloquean las confirmadas / en curso / pasadas.
NO_BLOQUEA = ("viaje solicitado", "cambio de viaje solicitado", "solicitud")
def bloquea(r):
    e = norm(r.get("estado"))
    return not any(k in e for k in NO_BLOQUEA)
res = []
_fant = []
for r in recs:
    if cancelada(r): continue
    if fantasma(r):
        _fant.append({"cod": r.get("codigo"), "huesped": abrev(r.get("huesped")), "visto": str(r.get("visto"))[:10],
                      "entrada": str(r.get("entrada"))[:10], "salida": str(r.get("salida"))[:10],
                      "estado": r.get("estado"), "anuncio": r.get("anuncio")})
        continue
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
                "estado": r.get("estado") or "", "bloquea": bloquea(r),
                # UNIDADES FÍSICAS: una reserva combo ocupa 2 deptos → son 2 limpiezas,
                # 2 llaves y 2 avisos a conserjería. Contar reservas descuadra la operación.
                "unid": max(1, len(r.get("deptos") or [])), "nums": list(r.get("deptos") or []),
                # habitación de hostal ≠ depto: no entra en rutas de limpieza de unidades
                "hab": bool(re.search(r"(cama en|habitaci[oó]n)", str(r.get("anuncio") or ""), re.I))})

# ---------- ocupación precomputada (por propiedad y día) ----------
ventana = [(HOY + timedelta(days=i)).isoformat() for i in range(DIAS_VENTANA)]
vset = set(ventana)
props.sort(key=lambda p: (p.get("externa", False), p["nombre"]))

_fant.sort(key=lambda x: x["visto"])
print(f"  ultimo barrido: {ULTIMO_BARRIDO} | reservas FANTASMA (vigentes pero ya no estan en Airbnb): {len(_fant)}")
json.dump(_fant, open(os.path.join(HERE, "reservas_fantasma.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)

# Las solicitudes que vencen desaparecen solas y nunca bloquearon: no son noticia.
# Una CONFIRMADA que desaparece sí lo es — o se canceló, o cambió de fechas. No se
# entierra en silencio: si el check-in está cerca, hay que confirmarla a mano.
fantasmas = [f for f in _fant if "onfirmada" in str(f["estado"])]
for f in fantasmas:
    try: f["dias"] = (date.fromisoformat(f["entrada"]) - HOY).days
    except Exception: f["dias"] = 999
fantasmas.sort(key=lambda x: x["dias"])
print(f"  confirmadas desaparecidas: {len(fantasmas)} | con check-in en <=7 dias: {sum(1 for f in fantasmas if f['dias'] <= 7)}")

# ---------- ocupación por UNIDAD FÍSICA ----------
# Un depto puede tener 2 anuncios (el original y su ESPEJO) y un anuncio puede cubrir 2
# deptos (los "combo"). Llevar la ocupación por anuncio miente en ambos sentidos: el espejo
# se ve libre con el depto tomado, y el combo bloquea uno cuando ocupa dos.
# La llave sale del REGISTRO, que marca ambos casos explícitamente. Nada se infiere por
# parecido de título: lo que el registro no cubre queda como unidad propia y se REPORTA.
POR_TIT, UNID, _hu = UN.cargar()
print(f"  registro: {len(UNID)} unidades fisicas / {len(POR_TIT)} anuncios" + (f" | sin resolver: {_hu}" if _hu else ""))

sin_registro = {}
for r in res:
    us = POR_TIT.get(UN.norm(r["anuncio"]))
    if not us:
        k = "s/reg|" + UN.norm(r["anuncio"])[:48]
        sin_registro.setdefault(UN.norm(r["anuncio"]), {"anuncio": r["anuncio"], "reservas": 0, "uid": k})
        sin_registro[UN.norm(r["anuncio"])]["reservas"] += 1
        us = [k]
    r["unids"] = us
    r["unid"] = len(us)          # cuántos deptos físicos ocupa esta reserva
    r["sinreg"] = us[0].startswith("s/reg|")

UMETA = dict(UNID)
for v in sin_registro.values():
    UMETA[v["uid"]] = {"edificio": v["anuncio"][:40], "depto": "", "cliente": "", "comuna": "",
                       "dir": "", "tipologia": "", "sin_registro": True}

# Un anuncio COMBO no es "una reserva que ocupa 2 deptos": Airbnb lo vende como POOL de 2
# unidades y varias reservas conviven en él. Y las unidades del pool también tienen anuncio
# propio. Entonces no se puede saber a qué depto fue cada huésped — y no hace falta:
# hay sobreventa cuando, para algún conjunto S de unidades, las reservas que SOLO pueden
# caer dentro de S superan el tamaño de S (condición de Hall). Eso no inventa asignaciones
# y no da falsos positivos.
from itertools import combinations
act = [r for r in res if r.get("bloquea") and r["entrada"]]
def noches(r):
    try:
        d0 = date.fromisoformat(r["entrada"])
        d1 = date.fromisoformat(r["salida"]) if r["salida"] else d0 + timedelta(days=1)
    except Exception: return []
    out, d = [], d0
    while d < d1:
        if d.isoformat() in vset: out.append(d.isoformat())
        d += timedelta(days=1)
    return out
for r in act: r["_noches"] = noches(r)

# componentes: unidades enlazadas por compartir algún anuncio
padre = {u: u for u in UMETA}
def raiz(x):
    while padre[x] != x: padre[x] = padre[padre[x]]; x = padre[x]
    return x
for r in act:
    us = [u for u in r["unids"] if u in padre]
    for u in us[1:]: padre[raiz(u)] = raiz(us[0])
comp = {}
for u in UMETA: comp.setdefault(raiz(u), []).append(u)

por_dia = {}
for r in act:
    for d in r["_noches"]: por_dia.setdefault(d, []).append(r)

solapes = []
for d, rs in por_dia.items():
    for _, units in comp.items():
        aqui = [r for r in rs if any(u in units for u in r["unids"])]
        if len(aqui) <= 1: continue
        k = len(units)
        for n in range(1, k + 1):
            for S in combinations(units, n):
                sS = set(S)
                dentro = [r for r in aqui if set(r["unids"]) <= sS]
                if len(dentro) > n:
                    solapes.append({"prop": " / ".join(
                        (UMETA[u]["edificio"] + (" · " + UMETA[u]["depto"] if UMETA[u]["depto"] else "")) for u in S),
                        "fecha": d, "a": dentro[0]["cod"], "b": dentro[1]["cod"],
                        "cupo": n, "reservas": len(dentro)})
                    break
            else: continue
            break

ocup_u = {u: {} for u in UMETA}
for r in act:
    for u in r["unids"]:
        for d in r["_noches"]: ocup_u[u].setdefault(d, {"cod": r["cod"], "h": r["huesped"], "pax": r["pax"]})

# el panel sigue mostrando por anuncio: la ocupación del anuncio = la de sus unidades
ocup = {p["id"]: {} for p in props}
for r in res:
    if not r["pid"]: continue
    for u in r["unids"]:
        for s_, v in ocup_u[u].items(): ocup[r["pid"]].setdefault(s_, v)

_vs, sol_u = set(), []
for c in solapes:
    k = tuple(sorted([c["a"], c["b"]]))
    if k in _vs: continue
    _vs.add(k); sol_u.append(c)
print(f"  solapes REALES (misma unidad fisica, ambas activas): {len(sol_u)}")
_sr = sorted(sin_registro.values(), key=lambda x: -x["reservas"])
print(f"  anuncios SIN fila en el registro: {len(_sr)} ({sum(x['reservas'] for x in _sr)} reservas)")
json.dump(_sr, open(os.path.join(HERE, "anuncios_sin_registro.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)

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

# ---------- estadía actual por propiedad + índice de reservas (para las urgencias) ----------
# Índice compacto por código: fechas, huésped, pax y propiedad. Lo usan las urgencias para
# mostrar quién está alojado AHORA, desde cuándo y hasta cuándo, con link a la reserva.
RES_IX = {}
for r in res:
    if r["cod"]:
        RES_IX[r["cod"]] = {"e": r["entrada"], "s": r["salida"], "h": r["huesped"],
                            "pax": r["pax"], "p": r["pnombre"], "pid": r["pid"]}

estadia = {}      # pid -> reserva que está ocupando HOY
hoy_s = HOY.isoformat()
for p in props:
    o = ocup.get(p["id"], {}).get(hoy_s)
    if o and o.get("cod"): estadia[p["id"]] = o["cod"]

# ---------- ACCESOS: reserva confirmada cuyo correo a conserjería NO se envió ----------
# Muchos edificios exigen que APTO mande los nombres ANTES del check-in; si no, el huésped
# queda en la puerta (es la incidencia de acceso más repetida del histórico).
def requiere_conserjeria(b):
    acc = (b.get("acceso") or {})
    return "conserjer" in norm(acc.get("clave_edificio")) + " " + norm(b.get("notas"))
REQ = {str(b.get("listing_id") or k) for k, b in prop.items()
       if isinstance(b, dict) and requiere_conserjeria(b)}

ACCF = os.path.join(HERE, "accesos_enviados.json")
acc_env, acc_resp, acc_auditado = set(), [], ""
if os.path.exists(ACCF):
    _a = json.load(open(ACCF, encoding="utf-8"))
    acc_env = {e.get("cod") for e in _a.get("enviados", []) if e.get("cod")}
    acc_resp = _a.get("respuestas_sin_contestar", [])
    acc_auditado = _a.get("_auditado", "")

VENTANA_ACC = 3          # avisar de los check-ins de hoy y los próximos 3 días
lim = (HOY + timedelta(days=VENTANA_ACC)).isoformat()
accesos_pend = []
for r in res:
    if not r["pid"] or r["pid"] not in REQ: continue
    if not (hoy_s <= r["entrada"] <= lim): continue
    if r["cod"] in acc_env: continue
    accesos_pend.append({"cod": r["cod"], "huesped": r["huesped"], "prop": r["pnombre"],
                         "dir": dir_txt(next((p for p in props if p["id"] == r["pid"]), {})),
                         "entrada": r["entrada"], "hin": r["hin"], "pax": r["pax"],
                         "hoy": r["entrada"] == hoy_s})
accesos_pend.sort(key=lambda x: (x["entrada"], x["hin"]))
print(f"  accesos SIN enviar (hoy→+{VENTANA_ACC}d): {len(accesos_pend)} | conserjería responde sin contestar: {len(acc_resp)}")

# teléfonos de huéspedes (se scrapean aparte a telefonos.json: {codigo: "+56..."} )
TELF = os.path.join(HERE, "telefonos.json")
tel = json.load(open(TELF, encoding="utf-8")) if os.path.exists(TELF) else {}
print(f"  estadías en curso: {len(estadia)} | teléfonos conocidos: {len(tel)}")

data = {
    "res_ix": RES_IX, "estadia": estadia, "tel": tel,
    "solapes": sol_u, "accesos_pend": accesos_pend, "acc_resp": acc_resp, "acc_auditado": acc_auditado,
    "generado": HOY.isoformat(),
    "ventana": {"desde": ventana[0], "hasta": ventana[-1], "dias": DIAS_VENTANA},
    "props": props, "reservas": res, "ocup": ocup, "agenda": agenda, "fantasmas": fantasmas,
    "insights": insights, "incidencias": incidencias, "semana": sem,
}
out = os.path.join(HERE, "datos.json")
json.dump(data, open(out, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
kb = os.path.getsize(out) / 1024
print(f"props {len(props)} | reservas {len(res)} | agenda(7d) {len(agenda)} | incid {len(incidencias)}")
print(f"ventana {ventana[0]} -> {ventana[-1]} | datos.json {kb:.0f} KB")
sinmatch = len([r for r in res if not r["pid"]])
print("reservas sin match a propiedad:", sinmatch)
