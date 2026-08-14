import json, os, sys, re, unicodedata
from datetime import date
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = r"C:\Users\Cami\Desktop\CLAUDE\APTO\Operacional\Cerebro_Turismo\Agente_Guest_Ops\scripts"
OUTDIR = r"C:\Users\Cami\Desktop\CLAUDE\APTO\Operacional\Cerebro_Turismo\panel_rutas"
os.makedirs(OUTDIR, exist_ok=True)

DIAS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
hoy = date.today()
HOY = hoy.isoformat()
HOY_TXT = f"{DIAS[hoy.weekday()]} {hoy.day} de {MESES[hoy.month-1]} de {hoy.year}"

ri = json.load(open(BASE + r"\reservas_index.json", encoding="utf-8"))
recs = list(ri.values()) if isinstance(ri, dict) else ri
prop = json.load(open(BASE + r"\propiedades.json", encoding="utf-8"))
bib = [v for v in prop.values() if isinstance(v, dict)]

def norm(s):
    return re.sub(r'[^a-z0-9 ]', '', unicodedata.normalize('NFKD', str(s or '')).encode('ascii', 'ignore').decode().lower()).strip()

def abrev(nombre):
    p = str(nombre or "").split()
    if not p: return "?"
    if len(p) == 1: return p[0]
    return p[0] + " " + p[1][0].upper() + "."

STOP = {"para", "con", "del", "los", "las", "una", "uno", "por", "que", "vista", "moderno", "moderna", "nuevo", "nueva", "gran", "amplio", "amplia", "comodo", "comoda"}
def toks(s): return set(t for t in norm(s).split() if len(t) > 2 and t not in STOP)
def match_biblia(anuncio):
    na = norm(anuncio)
    if not na: return None
    for v in bib:
        if norm(v.get("titulo_publico")) == na: return v
    ta = toks(anuncio)
    if not ta: return None
    best, bestsc = None, 0
    for v in bib:
        tv = toks(v.get("titulo_publico"))
        if tv and len(ta & tv) > bestsc: bestsc, best = len(ta & tv), v
    return best if bestsc >= 3 else None

# Suplemento V Región / Viña / Concón (fuera de la biblia), direcciones sacadas de los hilos.
SUP = [
    ("puertaroja", "Gálvez 25, Valparaíso (subir escaleras de Urriola)", "Valparaíso"),
    ("cerro concepcion", "Gálvez 35, Valparaíso (Cerro Concepción)", "Valparaíso"),
    ("vista al mar", "Calle de la Luna 77, Concón (ref. Resort Hipocampus)", "Concón"),
    ("central 2 autos", "Viña del Mar (depto completo)", "Viña del Mar"),
    ("plaza vina", "Plaza Viña del Mar", "Viña del Mar"),
    ("compartida", "Viña del Mar", "Viña del Mar"),
]
def comuna_kw(anuncio):
    n = norm(anuncio)
    for kw, c in [("vina", "Viña del Mar"), ("concon", "Concón"), ("nunoa", "Ñuñoa"),
                  ("condes", "Las Condes"), ("cerro concepcion", "Valparaíso"), ("providencia", "Providencia")]:
        if kw in n: return c
    return ""

def region(comuna, anuncio):
    c = norm(comuna); n = norm(anuncio)
    if any(k in c for k in ["valpara", "vina", "concon", "quilpue", "villa alemana"]): return "Quinta Región"
    if any(k in n for k in ["valpara", "vina", "concon", "cerro concepcion"]): return "Quinta Región"
    return "Santiago"

def hin(r): return r.get("hora_llegada") or "15:00"
def hout(r, m):
    if r.get("hora_salida"): return r["hora_salida"]
    if m and m.get("notas"):
        mm = re.search(r'out\s*(\d{1,2})[:h\.]?(\d{2})?', str(m["notas"]).lower())
        if mm: return f'{int(mm.group(1)):02d}:{mm.group(2) or "00"}'
    return "11:00" if "casa" in norm(r.get("anuncio")) else "12:00"

def park_info(anuncio, m):
    if m:
        est = (m.get("acceso") or {}).get("estacionamiento")
        if est and norm(est) not in ("no", "sin", "-", ""):
            num = re.search(r'n[°º]?\s*(\d+)', str(est).lower())
            return "N°" + num.group(1) if num else "sí"
    if "estacionamiento" in norm(anuncio) or "parking" in norm(anuncio): return "sí"
    return ""

def cancelada(r): return "cancel" in (r.get("estado") or "").lower()

def fila(r, tipo):
    m = match_biblia(r.get("anuncio"))
    direccion = (m.get("direccion") if m else None) or ""
    comuna = (m.get("comuna") if m else None) or ""
    interno = (m.get("nombre_interno") if m else None) or ""
    if not direccion:
        na = norm(r.get("anuncio"))
        for kw, d, c in SUP:
            if kw in na:
                direccion = d; comuna = comuna or c; break
    if not comuna: comuna = comuna_kw(r.get("anuncio"))
    return {"sec": "in" if tipo == "in" else "out",
            "hora": hin(r) if tipo == "in" else hout(r, m),
            "nombre": abrev(r.get("huesped")), "anuncio": r.get("anuncio") or "",
            "direccion": direccion, "comuna": comuna, "interno": interno,
            "region": region(comuna, r.get("anuncio")),
            "pax": r.get("adultos"), "park": park_info(r.get("anuncio"), m)}

cin = [fila(r, "in") for r in recs if str(r.get("entrada", ""))[:10] == HOY and not cancelada(r)]
cout = [fila(r, "out") for r in recs if str(r.get("salida", ""))[:10] == HOY and not cancelada(r)]

def sk(x):
    mm = re.search(r'(\d{1,2})[:h\.]?(\d{2})?', str(x.get("hora") or ""))
    return (0, int(mm.group(1)), int(mm.group(2) or 0)) if mm else (1, 0, 0)
cin.sort(key=sk); cout.sort(key=sk)

def esc(s): return str(s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def card(x):
    regcls = "st" if x["region"] == "Santiago" else "qr"
    dirl = esc(x["direccion"] or x["interno"] or x["anuncio"])
    comuna = f'<span class="comuna">{esc(x["comuna"])}</span>' if x["comuna"] else ""
    regb = f'<span class="reg {regcls}">{esc(x["region"])}</span>'
    pax = f'<span class="chip">👥 {x["pax"]}</span>' if x.get("pax") else ""
    park = f'<span class="chip park">🅿️ {esc(x["park"])}</span>' if x["park"] else ""
    sub = esc(x["anuncio"]) if (x["direccion"] and norm(x["anuncio"]) not in norm(x["direccion"])) else ""
    subd = f'<div class="anuncio">{sub}</div>' if sub else ''
    return f'''<div class="card {x['sec']}" data-region="{esc(x['region'])}">
      <div class="hora">{esc(x['hora'])}</div>
      <div class="info">
        <div class="dir">{dirl} {comuna} {regb}</div>
        <div class="meta"><span class="huesped">{esc(x['nombre'])}</span> {pax} {park}</div>
        {subd}
      </div>
    </div>'''

cin_html = "\n".join(card(x) for x in cin) or '<div class="vacio">Sin check-ins hoy</div>'
cout_html = "\n".join(card(x) for x in cout) or '<div class="vacio">Sin check-outs hoy</div>'

CSS = '''
:root{--bg:#f5f6f8;--card:#fff;--tx:#1a1d21;--mut:#6b7280;--in:#16a34a;--out:#ea8a1e;--line:#e5e7eb;--st:#2563eb;--qr:#9333ea}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,'Segoe UI',Roboto,sans-serif;background:var(--bg);color:var(--tx);padding:16px;max-width:640px;margin:0 auto;-webkit-font-smoothing:antialiased}
h1{font-size:1.35rem;font-weight:800;letter-spacing:-.02em}
.fecha{color:var(--mut);font-size:.9rem;margin-top:2px;text-transform:capitalize}
.gen{color:var(--mut);font-size:.72rem;margin-top:6px}
.filtros{display:flex;gap:8px;margin:16px 0 4px;flex-wrap:wrap}
.fbtn{border:1.5px solid var(--line);background:var(--card);color:var(--tx);font-weight:700;font-size:.85rem;padding:7px 15px;border-radius:22px;cursor:pointer;transition:.15s}
.fbtn.active{background:var(--tx);color:#fff;border-color:var(--tx)}
.fbtn[data-f="Santiago"].active{background:var(--st);border-color:var(--st)}
.fbtn[data-f="Quinta Región"].active{background:var(--qr);border-color:var(--qr)}
.sec{margin:22px 0 10px;font-size:.8rem;font-weight:800;letter-spacing:.06em;text-transform:uppercase;display:flex;align-items:center;gap:8px}
.sec .n{background:var(--tx);color:#fff;border-radius:20px;padding:1px 9px;font-size:.72rem}
.sec.i{color:var(--in)} .sec.o{color:var(--out)}
.card{background:var(--card);border-radius:14px;padding:12px 14px;margin-bottom:9px;display:flex;gap:13px;align-items:center;box-shadow:0 1px 3px rgba(0,0,0,.05);border-left:4px solid transparent}
.card.in{border-left-color:var(--in)} .card.out{border-left-color:var(--out)}
.hora{font-weight:800;font-size:1.1rem;min-width:58px;text-align:center;line-height:1.1}
.card.in .hora{color:var(--in)} .card.out .hora{color:var(--out)}
.info{flex:1;min-width:0}
.dir{font-weight:700;font-size:.98rem;line-height:1.3}
.comuna{display:inline-block;background:var(--line);color:var(--mut);font-size:.7rem;font-weight:700;padding:1px 7px;border-radius:10px;vertical-align:middle}
.reg{display:inline-block;font-size:.65rem;font-weight:800;padding:1px 7px;border-radius:10px;vertical-align:middle;color:#fff}
.reg.st{background:var(--st)} .reg.qr{background:var(--qr)}
.meta{margin-top:6px;display:flex;gap:6px;align-items:center;flex-wrap:wrap}
.huesped{color:var(--tx);font-weight:700;font-size:.9rem}
.chip{background:var(--line);color:var(--mut);font-size:.75rem;font-weight:600;padding:2px 8px;border-radius:10px}
.chip.park{background:#e0edff;color:#1d4ed8}
.anuncio{color:var(--mut);font-size:.76rem;margin-top:4px}
.vacio{color:var(--mut);font-style:italic;padding:8px 4px}
footer{margin-top:26px;color:var(--mut);font-size:.72rem;text-align:center;border-top:1px solid var(--line);padding-top:12px}
@media(prefers-color-scheme:dark){:root{--bg:#111418;--card:#1b1f24;--tx:#e8eaed;--mut:#9aa0a6;--line:#2a2f36}.chip.park{background:#16305c;color:#93c5fd}}
'''

JS = '''
function apply(f){
  ["in","out"].forEach(function(s){
    var n=0;
    document.querySelectorAll(".card."+s).forEach(function(c){
      var show=(f==="all"||c.dataset.region===f);
      c.style.display=show?"":"none"; if(show)n++;
    });
    var chip=document.querySelector(".sec."+(s==="in"?"i":"o")+" .n");
    if(chip) chip.textContent=n;
  });
}
document.querySelectorAll(".fbtn").forEach(function(b){
  b.onclick=function(){
    document.querySelectorAll(".fbtn").forEach(function(x){x.classList.remove("active")});
    b.classList.add("active");
    apply(b.dataset.f);
  };
});
'''

html = f'''<!doctype html><html lang="es"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Rutas del dia - APTO</title>
<style>{CSS}</style></head><body>
<header>
  <h1>🚐 Rutas del día · APTO</h1>
  <div class="fecha">{HOY_TXT}</div>
  <div class="gen">Nombres abreviados por privacidad · horas estándar salvo que el huésped coordine otra · uso interno</div>
</header>
<div class="filtros">
  <button class="fbtn active" data-f="all">Todos</button>
  <button class="fbtn" data-f="Santiago">Santiago</button>
  <button class="fbtn" data-f="Quinta Región">Quinta Región</button>
</div>
<div class="sec i">🟢 Check-in · llegadas <span class="n">{len(cin)}</span></div>
{cin_html}
<div class="sec o">🟠 Check-out · salidas <span class="n">{len(cout)}</span></div>
{cout_html}
<footer>APTO · panel de rutas — se actualiza solo cada día · check-in desde 15:00, check-out según propiedad</footer>
<script>{JS}</script>
</body></html>'''

open(os.path.join(OUTDIR, "index.html"), "w", encoding="utf-8").write(html)
print("Fecha:", HOY_TXT)
print("check-ins:", len(cin), "| check-outs:", len(cout))
print("Regiones in:", {r["region"] for r in cin}, "| out:", {r["region"] for r in cout})
