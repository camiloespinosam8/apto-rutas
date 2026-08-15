# unidades.py — Resuelve ANUNCIO → UNIDAD(ES) FÍSICA(S).
#
# Por qué existe: un depto puede tener VARIOS anuncios (el original + su ESPEJO), y un
# anuncio puede cubrir VARIOS deptos (los "combo"). Si la ocupación se lleva por anuncio,
# el calendario miente en las dos direcciones: el espejo aparece libre cuando el depto ya
# está tomado, y el combo bloquea uno solo cuando en realidad ocupa dos.
#
# La verdad es el REGISTRO (registro_anuncios_apto.csv), que YA marca ambos casos:
#   depto = "combo 1615+401"   → el anuncio ocupa las unidades 1615 y 401
#   depto = "402 (ESPEJO)"     → el anuncio es un espejo de la unidad 402
# No se infiere NADA por parecido de título. Lo que no está en el registro queda como
# unidad propia y se reporta aparte para que Camilo lo mapee a mano.
import csv, os, re, unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
REGF = os.path.join(HERE, "..", "..", "Sistema_Reservas", "anuncios", "registro_anuncios_apto.csv")


def norm(s):
    s = unicodedata.normalize("NFKD", str(s or "")).encode("ascii", "ignore").decode().lower()
    return " ".join(s.split())


def _edificio(dirn):
    """Nombre corto y estable del edificio/casa, para armar el id de unidad."""
    d = str(dirn or "").strip()
    d = re.sub(r'^(CASA PROPIA de APTO|ESPEJO de\s*\d*|ESPEJO)\s*[—·-]*\s*', '', d, flags=re.I)
    d = re.sub(r'^⚠️?\s*', '', d)
    d = re.split(r'\s*[·—]\s*|\s*\(', d)[0]
    d = re.sub(r'\s+(depto|dpto)\s+\S+$', '', d, flags=re.I)
    return " ".join(d.split())[:40] or "?"


def cargar():
    """-> (por_titulo, unidades, sin_direccion)

    por_titulo: título normalizado -> lista de ids de unidad física que ocupa
    unidades:   id de unidad -> {"edificio","depto","tipologia","cliente","comuna","dir"}
    """
    rows = list(csv.DictReader(open(REGF, encoding="utf-8-sig")))
    unidades, por_titulo, huerfanos = {}, {}, []

    def es_espejo(r):
        return "espejo" in norm(r["depto"]) or norm(r["direccion_notas"]).startswith("espejo") \
            or "espejo de" in norm(r["direccion_notas"])

    def es_combo(r):
        return norm(r["depto"]).startswith("combo")

    def nuevo(r, dep, edif):
        """Cada fila NO-espejo del registro es, por definición, una unidad distinta.
        El id lleva el listing_id para que dos casas del MISMO terreno (El Cerro 0348
        tiene dos, con patio compartido) jamás se fusionen por compartir dirección."""
        u = f"{norm(edif)}|{norm(dep)}|{str(r['listing_id'])[-6:]}"
        unidades[u] = {"edificio": edif, "depto": dep, "tipologia": r["tipologia"],
                       "cliente": r["cliente"], "comuna": r["comuna"], "dir": r["direccion_notas"],
                       "limpieza": r.get("costo_limpieza"), "listing": r["listing_id"]}
        return u

    def buscar(dep, cliente, edif=""):
        """Unidad ya existente por n° de depto. Desempata por cliente y luego por edificio;
        si queda ambiguo devuelve None y el caso se reporta, no se adivina."""
        d = norm(re.sub(r'\s*\(espejo\)', '', str(dep), flags=re.I))
        c = [u for u, v in unidades.items() if norm(v["depto"]) == d]
        # El DUEÑO manda: el 713 de Diego (Campo de Deportes 80) no es el 713 de Finaldi
        # (VM920) aunque el número coincida. Si el cliente no calza, no es la misma unidad.
        if cliente:
            c = [u for u in c if norm(unidades[u]["cliente"])[:10] == norm(cliente)[:10]] or []
        if len(c) == 1: return c[0]
        if len(c) > 1 and edif:
            f = [u for u in c if norm(edif) and norm(edif) in u]
            if len(f) == 1: return f[0]
        return None

    # 1) unidades reales: una fila = una unidad. Nada se fusiona acá.
    for r in rows:
        if es_espejo(r) or es_combo(r): continue
        u = nuevo(r, r["depto"].strip(), _edificio(r["direccion_notas"]))
        por_titulo.setdefault(norm(r["titulo_actual"]), []).append(u)

    # 2) combos: apuntan a unidades YA existentes ("combo 1615+401" = las unidades 1615 y 401
    #    del mismo cliente). Solo si el depto no existe en ninguna parte se crea.
    for r in rows:
        if not es_combo(r): continue
        edif = _edificio(r["direccion_notas"])
        ds = re.findall(r'[A-Za-z]?\d+[A-Za-z]?', r["depto"][5:])
        us = []
        for d in ds:
            u = buscar(d, r["cliente"], edif)
            us.append(u or nuevo(r, d, edif))
        por_titulo[norm(r["titulo_actual"])] = us

    # 3) espejos: NUNCA crean unidad. Se resuelven por n° de depto o por el listing_id que
    #    la propia nota declara ("ESPEJO de <listing_id>"). Si no resuelve, se reporta.
    for r in rows:
        if not es_espejo(r): continue
        t = norm(r["titulo_actual"])
        u = buscar(r["depto"], r["cliente"], _edificio(r["direccion_notas"]))
        if not u:
            m = re.search(r'espejo de\s*(\d{6,})', norm(r["direccion_notas"]))
            if m:
                pref = m.group(1)[:12]
                o = [x for x, v in unidades.items() if str(v["listing"]).startswith(pref)]
                if len(o) == 1: u = o[0]
        if u:
            por_titulo.setdefault(t, [])
            if u not in por_titulo[t]: por_titulo[t].append(u)
        else:
            huerfanos.append(r["titulo_actual"] + "  (espejo sin original resuelto)")

    return por_titulo, unidades, huerfanos


if __name__ == "__main__":
    import sys, collections
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    pt, un, hu = cargar()
    print(f"unidades físicas: {len(un)}   anuncios mapeados: {len(pt)}")
    multi = {t: v for t, v in pt.items() if len(v) > 1}
    print(f"\nanuncios COMBO (ocupan 2 unidades): {len(multi)}")
    for t, v in multi.items():
        print(f"   {t[:56]:58s} -> {', '.join(v)}")
    inv = collections.defaultdict(list)
    for t, v in pt.items():
        if len(v) == 1:
            inv[v[0]].append(t)
    print("\nunidades con MÁS DE UN anuncio (espejos):")
    for u, ts in inv.items():
        if len(ts) > 1:
            print(f"   {u}")
            for t in ts:
                print(f"        · {t[:64]}")
    if hu:
        print("\nfilas del registro SIN unidad resuelta:", hu)
