# build_panel.py — Centro de control APTO. Diseño "manifiesto operacional":
# filas densas con filetes, números tabulares, paleta de marca APTO (crema/ladrillo/tinta).
# Interno: sin texto explicativo, todo escaneable. Datos precalculados desde datos.json.
import json, os, sys
from datetime import date
from fecha_chile import hoy_chile
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = os.path.dirname(os.path.abspath(__file__))
D = json.load(open(os.path.join(HERE, "datos.json"), encoding="utf-8"))

DIAS = ["lunes","martes","miércoles","jueves","viernes","sábado","domingo"]
MESES = ["ene","feb","mar","abr","may","jun","jul","ago","sep","oct","nov","dic"]
h = date.fromisoformat(D["generado"])
FECHA_TXT = f"{DIAS[h.weekday()]} {h.day} {MESES[h.month-1]}"

CSS = """
:root{
  --crema:#F4EFE6; --papel:#FBF9F4; --tinta:#1D1D1B; --mute:#6B6256; --linea:#E7DCC9;
  --ladrillo:#C8572A; --vino:#9B3A2E; --exito:#2F7D5B;
  --z-sticky:100; --z-pop:300;
  --ease:cubic-bezier(.22,1,.36,1);
}
*{box-sizing:border-box;margin:0;padding:0}
html{-webkit-text-size-adjust:100%}
body{
  font-family:Manrope,-apple-system,'Segoe UI',Roboto,sans-serif;
  background:var(--crema); color:var(--tinta);
  font-size:15px; line-height:1.45; -webkit-font-smoothing:antialiased;
  padding:0 0 40px; max-width:1120px; margin:0 auto;
}
.wrap{padding:0 16px}
/* ---- cabecera ---- */
header{padding:20px 16px 12px;display:flex;align-items:baseline;justify-content:space-between;gap:12px}
.mark{font-family:'Playfair Display',Georgia,serif;font-weight:800;font-size:1.9rem;letter-spacing:.09em;line-height:1}
.hoy{font-size:.82rem;color:var(--mute);font-variant-numeric:tabular-nums;white-space:nowrap}
/* ---- pestañas ---- */
.tabs{position:sticky;top:0;z-index:var(--z-sticky);background:var(--crema);
  display:flex;gap:2px;padding:6px 16px 8px;overflow-x:auto;scrollbar-width:none;
  border-bottom:1px solid var(--linea)}
.tabs::-webkit-scrollbar{display:none}
.tab{white-space:nowrap;border:0;background:transparent;color:var(--mute);
  font-family:inherit;font-weight:700;font-size:.88rem;padding:8px 12px;border-radius:7px;
  cursor:pointer;transition:color .18s var(--ease),background .18s var(--ease)}
.tab:hover{color:var(--tinta)}
.tab[aria-selected="true"]{background:var(--ladrillo);color:var(--papel)}
.tab:focus-visible{outline:2px solid var(--ladrillo);outline-offset:2px}
.pane{display:none;padding-top:14px} .pane.on{display:block}
/* ---- controles ---- */
.bar{display:flex;gap:7px;flex-wrap:wrap;align-items:center;margin-bottom:12px}
input,select,button.go{font:inherit;color:var(--tinta);background:var(--papel);
  border:1px solid var(--linea);border-radius:8px;padding:9px 11px;min-height:40px}
input::placeholder{color:var(--mute)}
input:focus,select:focus{outline:2px solid var(--ladrillo);outline-offset:-1px;border-color:transparent}
.grow{flex:1 1 200px;min-width:0}
button.go{background:var(--tinta);color:var(--papel);border-color:var(--tinta);font-weight:700;cursor:pointer}
.q{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:12px}
.q button{font:inherit;font-size:.82rem;font-weight:700;color:var(--vino);background:transparent;
  border:1px solid var(--linea);border-radius:99px;padding:6px 13px;cursor:pointer;
  transition:background .18s var(--ease),color .18s var(--ease),border-color .18s var(--ease)}
.q button:hover{background:var(--vino);color:var(--papel);border-color:var(--vino)}
/* ---- filas (NO cards) ---- */
.count{font-size:.8rem;color:var(--mute);font-variant-numeric:tabular-nums;margin:14px 0 4px}
.count b{color:var(--tinta)}
.rows{border-top:1px solid var(--linea)}
.r{display:flex;gap:12px;align-items:baseline;padding:11px 2px;border-bottom:1px solid var(--linea)}
.r:hover{background:var(--papel)}
.t{font-variant-numeric:tabular-nums;font-weight:800;font-size:1.02rem;min-width:52px;letter-spacing:-.01em}
.t.in{color:var(--exito)} .t.out{color:var(--vino)}
.m{flex:1;min-width:0}
.n{font-weight:700;letter-spacing:-.01em}
.d{font-size:.85rem;color:var(--mute);margin-top:1px;font-variant-numeric:tabular-nums}
.tags{display:flex;gap:5px;align-items:center;flex-wrap:wrap;flex-shrink:0}
.tg{font-size:.74rem;font-weight:700;color:var(--mute);font-variant-numeric:tabular-nums;white-space:nowrap}
.tg.p{color:var(--vino)}
.tg.reg{color:var(--mute);opacity:.75}
/* ---- desplegable de ficha ---- */
details.r{display:block;padding:0}
details.r>summary{list-style:none;cursor:pointer;display:flex;gap:12px;align-items:baseline;padding:11px 2px}
details.r>summary::-webkit-details-marker{display:none}
details.r[open]{background:var(--papel)}
.kv{display:grid;grid-template-columns:88px 1fr;gap:2px 12px;padding:2px 2px 13px;font-size:.85rem}
.kv dt{color:var(--mute);font-weight:600}
.kv dd{font-variant-numeric:tabular-nums;word-break:break-word}
.kv a{color:var(--vino)}
/* ---- día ---- */
.day{font-family:'Playfair Display',Georgia,serif;font-size:1.15rem;font-weight:700;
  margin:20px 0 2px;display:flex;align-items:baseline;gap:9px}
.day span{font-family:Manrope,sans-serif;font-size:.78rem;font-weight:600;color:var(--mute);font-variant-numeric:tabular-nums}
/* ---- ranking ---- */
table{width:100%;border-collapse:collapse;font-size:.87rem;font-variant-numeric:tabular-nums}
th{text-align:left;padding:8px 8px 8px 0;font-size:.74rem;font-weight:800;color:var(--mute);
  border-bottom:1px solid var(--linea);cursor:pointer;white-space:nowrap;user-select:none}
th:hover{color:var(--ladrillo)}
th[aria-sort]{color:var(--ladrillo)}
td{padding:9px 8px 9px 0;border-bottom:1px solid var(--linea)}
td:first-child{color:var(--mute);width:26px}
.bar2{height:6px;background:var(--linea);border-radius:99px;overflow:hidden;min-width:44px}
.bar2>i{display:block;height:100%;background:var(--ladrillo)}
/* ---- calendario ---- */
.cal{overflow-x:auto;padding-bottom:6px}
.cg{display:grid;gap:1px;min-width:720px}
.c{height:22px;border-radius:2px;background:#E9E0CE}
.c.b{background:var(--vino)}
.c.h{background:transparent;font-size:.6rem;color:var(--mute);text-align:center;height:auto;font-weight:700;font-variant-numeric:tabular-nums}
.c.h.w{color:var(--ladrillo)}
.cn{font-size:.72rem;font-weight:700;line-height:22px;padding-right:8px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.leg{display:flex;gap:14px;font-size:.76rem;color:var(--mute);margin:6px 0 8px}
.leg i{display:inline-block;width:10px;height:10px;border-radius:2px;margin-right:5px;vertical-align:-1px}
/* ---- incidencias ---- */
.sev{font-size:.7rem;font-weight:800;font-variant-numeric:tabular-nums}
.sev.alta{color:var(--vino)} .sev.media{color:var(--ladrillo)} .sev.baja{color:var(--exito)}
.acc{font-size:.85rem;margin-top:5px;padding-left:11px;border-left:1px solid var(--linea);color:var(--mute)}
.acc b{color:var(--tinta);font-weight:700}
.cats{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:6px}
.cats button{font:inherit;font-size:.82rem;font-weight:700;background:transparent;border:1px solid var(--linea);
  color:var(--mute);border-radius:99px;padding:6px 12px;cursor:pointer}
.cats button[aria-pressed="true"]{background:var(--tinta);color:var(--papel);border-color:var(--tinta)}
.none{color:var(--mute);padding:22px 2px;font-size:.88rem}
footer{color:var(--mute);font-size:.72rem;padding:22px 16px 0;font-variant-numeric:tabular-nums}
@media (prefers-reduced-motion:reduce){*{transition:none!important;animation:none!important}}
"""

JS = r"""
const D=window.__D__, $=s=>document.querySelector(s);
const esc=s=>String(s==null?'':s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const nrm=s=>String(s||'').normalize('NFD').replace(/\p{Diacritic}/gu,'').toLowerCase();
const clp=n=>{const v=Number(n);return Number.isFinite(v)&&v>0?('$'+v.toLocaleString('es-CL')):''};
const VAC=new Set(['','-','—','s/n','sn','casa','none','null','?']);
const ok=v=>{const s=String(v==null?'':v).trim();return VAC.has(s.toLowerCase())?'':s};

// dirección compacta: Calle N°, depto X, Comuna
function dir(p){
  const a=[],c=[ok(p.calle),ok(p.numero)].filter(Boolean).join(' ');
  if(c)a.push(c); if(ok(p.depto))a.push('depto '+ok(p.depto)); if(ok(p.comuna))a.push(ok(p.comuna));
  return a.join(', ');
}
function tagsProp(p){
  const t=[];
  if(p.activo===false)t.push('<span class="tg" style="color:var(--vino)">inactivo</span>');
  if(p.cap)t.push(`<span class="tg">${p.cap}p</span>`);
  if(p.park&&p.park.tiene)t.push(`<span class="tg p">P${p.park.num?' '+p.park.num:''}</span>`);
  if(Number(p.rating)>0)t.push(`<span class="tg">${p.rating}★</span>`);
  return t.join('');
}
// ---- tabs ----
document.querySelectorAll('.tab').forEach(b=>b.onclick=()=>{
  document.querySelectorAll('.tab').forEach(x=>x.setAttribute('aria-selected','false'));
  document.querySelectorAll('.pane').forEach(x=>x.classList.remove('on'));
  b.setAttribute('aria-selected','true'); $('#p'+b.dataset.t).classList.add('on');
});
// ---- 1 propiedades ----
function rowProp(p){
  const kv=[['Dirección',dir(p)],['Clave edif.',ok(p.acceso.edificio)],['Clave depto',ok(p.acceso.depto)],
    ['WiFi',ok(p.wifi.red)?(p.wifi.red+' · '+p.wifi.clave):''],['Camas',ok(p.camas)],
    ['Estac.',ok(p.acceso.estacionamiento)||(p.park.tiene?'sí':'')],['Limpieza',clp(p.limpieza)],
    ['Responsable',ok(p.responsable)],['Dueño',ok(p.dueno)]]
    .filter(([,v])=>v).map(([k,v])=>`<dt>${k}</dt><dd>${esc(v)}</dd>`).join('');
  return `<details class="r"><summary>
      <div class="m"><div class="n">${esc(p.nombre)}</div><div class="d">${esc(dir(p)||ok(p.comuna))}</div></div>
      <div class="tags">${tagsProp(p)}</div></summary>
      <dl class="kv">${kv}${p.url?`<dt>Anuncio</dt><dd><a href="${p.url}" target="_blank" rel="noopener">abrir ↗</a></dd>`:''}</dl>
    </details>`;
}
function renderProps(){
  const q=nrm($('#qp').value),reg=$('#fr').value;
  const o=D.props.filter(p=>(reg==='all'||p.region===reg)&&(!q||nrm([p.nombre,p.calle,p.numero,p.depto,p.comuna,p.interno,p.dueno].join(' ')).includes(q)));
  $('#np').textContent=o.length;
  $('#lp').innerHTML=o.length?o.map(rowProp).join(''):'<div class="none">Sin resultados</div>';
}
// ---- 2 movimientos ----
function renderAg(){
  const f=$('#fa').value,reg=$('#far').value;
  const dias=f==='hoy'?[D.semana[0]]:D.semana;
  let h='';
  dias.forEach(d=>{
    const it=D.agenda.filter(a=>a.fecha===d&&(reg==='all'||a.region===reg));
    if(f==='hoy'||it.length){
      const dt=new Date(d+'T12:00:00'),nm=['dom','lun','mar','mié','jue','vie','sáb'][dt.getDay()];
      h+=`<div class="day">${nm} ${dt.getDate()}<span>${it.length} mov</span></div><div class="rows">`;
      h+=it.length?it.map(a=>`<div class="r"><div class="t ${a.tipo}">${esc(a.hora)}</div>
        <div class="m"><div class="n">${esc(a.dir||a.pnombre)}</div>
        <div class="d">${a.tipo==='in'?'entra':'sale'} ${esc(a.huesped)}${a.pax?' · '+a.pax+'p':''}</div></div></div>`).join('')
        :'<div class="none">Sin movimientos</div>';
      h+='</div>';
    }
  });
  $('#la').innerHTML=h||'<div class="none">Sin movimientos</div>';
}
// ---- 3 disponibilidad (precomputada) ----
const NC=45;
function fechas(n){const a=[],d=new Date(D.ventana.desde+'T12:00:00');for(let i=0;i<n;i++){a.push(d.toISOString().slice(0,10));d.setDate(d.getDate()+1)}return a}
function renderCal(){
  const reg=$('#fcr').value,ds=fechas(NC),ps=D.props.filter(p=>reg==='all'||p.region===reg);
  let h=`<div class="cg" style="grid-template-columns:132px repeat(${NC},1fr)"><div class="c h"></div>`;
  h+=ds.map(d=>{const t=new Date(d+'T12:00:00'),w=t.getDay()===0||t.getDay()===6;
    return `<div class="c h${w?' w':''}">${t.getDate()}</div>`}).join('');
  ps.forEach(p=>{
    h+=`<div class="cn" title="${esc(p.nombre)}">${esc(p.nombre)}</div>`;
    h+=ds.map(d=>{const o=(D.ocup[p.id]||{})[d];
      return `<div class="c${o?' b':''}" title="${esc(p.nombre)} · ${d}${o?' · '+esc(o.h):' · libre'}"></div>`}).join('');
  });
  $('#cg').innerHTML=h+'</div>';
}
function libres(de,ha,pax,reg,pk){
  const out=[],d0=new Date(de+'T12:00:00'),d1=new Date(ha+'T12:00:00');
  D.props.forEach(p=>{
    if(reg!=='all'&&p.region!==reg)return;
    if(pax&&(!p.cap||p.cap<pax))return;
    if(pk&&!(p.park&&p.park.tiene))return;
    let ok=true;const d=new Date(d0);
    while(d<d1){if((D.ocup[p.id]||{})[d.toISOString().slice(0,10)]){ok=false;break}d.setDate(d.getDate()+1)}
    if(ok)out.push(p);
  });
  return out;
}
function correr(){
  const de=$('#qd').value,ha=$('#qh').value;
  if(!de||!ha){$('#qr').innerHTML='<div class="none">Elige fechas</div>';return}
  const pax=parseInt($('#qx').value)||0,reg=$('#qg').value,pk=$('#qk').checked;
  const r=libres(de,ha,pax,reg,pk),n=Math.round((new Date(ha)-new Date(de))/864e5);
  $('#qr').innerHTML=`<div class="count"><b>${r.length}</b> libres · ${n} noche${n===1?'':'s'}${pax?' · '+pax+'p':''}${pk?' · con P':''}</div>`+
    (r.length?'<div class="rows">'+r.map(p=>`<div class="r"><div class="m"><div class="n">${esc(p.nombre)}</div>
      <div class="d">${esc(dir(p)||ok(p.comuna))}</div></div><div class="tags">${tagsProp(p)}</div></div>`).join('')+'</div>'
    :'<div class="none">Nada libre con esos filtros</div>');
}
function preset(dd,nn,pax,pk){
  const d=new Date(D.ventana.desde+'T12:00:00');d.setDate(d.getDate()+dd);
  const f=new Date(d);f.setDate(f.getDate()+nn);
  $('#qd').value=d.toISOString().slice(0,10);$('#qh').value=f.toISOString().slice(0,10);
  $('#qx').value=pax||'';$('#qk').checked=!!pk;correr();
}
// ---- 4 ranking ----
let sk='rating',sd=-1;
function renderIns(){
  const reg=$('#fir').value;
  const rows=D.insights.filter(i=>reg==='all'||i.region===reg).sort((a,b)=>{
    let x=a[sk],y=b[sk];if(x==null)x=-1;if(y==null)y=-1;
    return typeof x==='string'?sd*x.localeCompare(y):sd*(x-y)});
  $('#tb').innerHTML=rows.map((i,n)=>`<tr><td>${n+1}</td>
    <td><b>${esc(i.nombre)}</b></td><td>${i.rating?i.rating+'★':'—'}</td><td>${i.nresenas??'—'}</td>
    <td>${i.cap||'—'}</td><td><div style="display:flex;align-items:center;gap:7px">
    <div class="bar2"><i style="width:${i.ocup_pct}%"></i></div>${i.ocup_pct}%</div></td>
    <td>${clp(i.limpieza)||'—'}</td></tr>`).join('');
  document.querySelectorAll('th[data-k]').forEach(t=>{
    if(t.dataset.k===sk)t.setAttribute('aria-sort',sd<0?'descending':'ascending');else t.removeAttribute('aria-sort')});
}
document.querySelectorAll('th[data-k]').forEach(t=>t.onclick=()=>{
  const k=t.dataset.k;sd=(sk===k)?-sd:-1;sk=k;renderIns()});
// ---- 5 incidencias ----
const CN={insumos:'Insumos',higiene:'Higiene',tecnico:'Técnico',acceso:'Acceso',otros:'Otros'};
let cat='all', soloAbiertas=true;
function renderInc(){
  const rows=D.incidencias.filter(i=>(cat==='all'||i.cat===cat)&&(!soloAbiertas||i.estado!=='resuelto'));
  const nAb=D.incidencias.filter(i=>i.estado!=='resuelto').length;
  $('#ic').innerHTML=`<b>${rows.length}</b> de ${D.incidencias.length} · ${nAb} sin resolver`;
  $('#li').innerHTML=rows.length?'<div class="rows">'+rows.map(i=>`<div class="r">
    <div class="t ${i.sev==='alta'?'out':'in'}" style="font-size:.7rem;font-weight:800;min-width:56px">${CN[i.cat]||i.cat}</div>
    <div class="m"><div class="n">${esc(i.titulo)}</div>
      <div class="d">${esc(i.prop)}${i.huesped?' · '+esc(i.huesped):''} · ${esc(i.fecha)}</div>
      ${i.cita?`<div class="d" style="font-style:italic">«${esc(i.cita)}»</div>`:''}
      <div class="acc"><b>→</b> ${esc(i.accion)}</div></div>
    <div class="tags"><span class="sev ${i.sev}">${esc(i.sev)}</span>
      <span class="tg" style="color:${i.estado==='resuelto'?'var(--exito)':'var(--vino)'}">${esc(i.estado)}</span></div></div>`).join('')+'</div>'
    :'<div class="none">Sin incidencias</div>';
}
$('#iab').onclick=e=>{soloAbiertas=!soloAbiertas;
  e.target.setAttribute('aria-pressed',soloAbiertas?'true':'false');
  e.target.textContent=soloAbiertas?'Solo sin resolver':'Todas';renderInc()};
document.querySelectorAll('.cats button').forEach(b=>b.onclick=()=>{
  document.querySelectorAll('.cats button').forEach(x=>x.setAttribute('aria-pressed','false'));
  b.setAttribute('aria-pressed','true');cat=b.dataset.c;renderInc()});
['qp','fr'].forEach(i=>$('#'+i).addEventListener('input',renderProps));
['fa','far'].forEach(i=>$('#'+i).addEventListener('input',renderAg));
$('#fcr').addEventListener('input',renderCal);$('#fir').addEventListener('input',renderIns);
$('#go').onclick=correr;
document.querySelectorAll('.q button').forEach(b=>b.onclick=()=>preset(+b.dataset.d,+b.dataset.n,+b.dataset.p,b.dataset.k==='1'));
renderProps();renderAg();renderCal();renderIns();renderInc();
$('#qd').value=D.ventana.desde;
const t=new Date(D.ventana.desde+'T12:00:00');t.setDate(t.getDate()+2);$('#qh').value=t.toISOString().slice(0,10);
correr();
"""

cats = {}
for i in D["incidencias"]: cats[i["cat"]] = cats.get(i["cat"], 0) + 1
catbtn = "".join(f'<button data-c="{k}" aria-pressed="false">{n} <span style="opacity:.6">{cats.get(k,0)}</span></button>'
                 for k, n in [("insumos","Insumos"),("higiene","Higiene"),("tecnico","Técnico"),("acceso","Acceso"),("otros","Otros")])

html = f"""<!doctype html><html lang="es"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>APTO · control</title>
<meta name="theme-color" content="#F4EFE6">
<meta name="robots" content="noindex,nofollow,noarchive">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Manrope:wght@500;600;700;800&family=Playfair+Display:wght@700;800&display=swap" rel="stylesheet">
<style>{CSS}</style></head><body>
<header><div class="mark">APTO</div><div class="hoy">{FECHA_TXT} · {len(D['props'])} propiedades</div></header>

<div class="tabs" role="tablist">
  <button class="tab" role="tab" aria-selected="true" data-t="1">Propiedades</button>
  <button class="tab" role="tab" aria-selected="false" data-t="2">Movimientos</button>
  <button class="tab" role="tab" aria-selected="false" data-t="3">Disponibilidad</button>
  <button class="tab" role="tab" aria-selected="false" data-t="4">Ranking</button>
  <button class="tab" role="tab" aria-selected="false" data-t="5">Incidencias</button>
</div>

<div class="wrap">
<section class="pane on" id="p1">
  <div class="bar">
    <input id="qp" class="grow" placeholder="Buscar calle, comuna, depto…" autocomplete="off">
    <select id="fr"><option value="all">Todas</option><option>Santiago</option><option>Quinta Región</option></select>
  </div>
  <div class="count"><b id="np">0</b> propiedades</div>
  <div class="rows" id="lp"></div>
</section>

<section class="pane" id="p2">
  <div class="bar">
    <select id="fa"><option value="hoy">Hoy</option><option value="semana">7 días</option></select>
    <select id="far"><option value="all">Todas</option><option>Santiago</option><option>Quinta Región</option></select>
  </div>
  <div id="la"></div>
</section>

<section class="pane" id="p3">
  <div class="q">
    <button data-d="0" data-n="1" data-p="0" data-k="0">Hoy</button>
    <button data-d="1" data-n="1" data-p="0" data-k="0">Mañana</button>
    <button data-d="0" data-n="2" data-p="4" data-k="0">4p · 2n</button>
    <button data-d="0" data-n="2" data-p="4" data-k="1">4p · 2n · P</button>
    <button data-d="0" data-n="3" data-p="6" data-k="0">6p · 3n</button>
    <button data-d="0" data-n="7" data-p="8" data-k="0">8p · 7n</button>
  </div>
  <div class="bar">
    <input type="date" id="qd"><input type="date" id="qh">
    <input type="number" id="qx" placeholder="pax" min="1" style="max-width:88px">
    <select id="qg"><option value="all">Todas</option><option>Santiago</option><option>Quinta Región</option></select>
    <label style="display:flex;align-items:center;gap:6px;font-size:.85rem;font-weight:700"><input type="checkbox" id="qk" style="min-height:0;width:auto"> P</label>
    <button class="go" id="go">Buscar</button>
  </div>
  <div id="qr"></div>
  <div class="day" style="margin-top:24px">Ocupación<span>45 días</span></div>
  <div class="bar"><select id="fcr"><option value="all">Todas</option><option>Santiago</option><option>Quinta Región</option></select></div>
  <div class="leg"><span><i style="background:#E9E0CE"></i>libre</span><span><i style="background:#9B3A2E"></i>ocupado</span></div>
  <div class="cal"><div id="cg"></div></div>
</section>

<section class="pane" id="p4">
  <div class="bar"><select id="fir"><option value="all">Todas</option><option>Santiago</option><option>Quinta Región</option></select></div>
  <table><thead><tr><th></th><th data-k="nombre">Propiedad</th><th data-k="rating">★</th><th data-k="nresenas">Reseñas</th>
    <th data-k="cap">Pax</th><th data-k="ocup_pct">Ocupación</th><th data-k="limpieza">Limpieza</th></tr></thead>
    <tbody id="tb"></tbody></table>
</section>

<section class="pane" id="p5">
  <div class="cats"><button data-c="all" aria-pressed="true">Todas <span style="opacity:.6">{len(D['incidencias'])}</span></button>{catbtn}
    <button id="iab" aria-pressed="true" style="margin-left:auto">Solo sin resolver</button></div>
  <div class="count" id="ic"></div>
  <div id="li"></div>
</section>
</div>

<footer>Actualizado {D['generado']} · datos precalculados</footer>
<script>window.__D__={json.dumps(D, ensure_ascii=False, separators=(',',':'))};</script>
<script>{JS}</script>
</body></html>"""

out = os.path.join(HERE, "panel.html")
open(out, "w", encoding="utf-8").write(html)
print(f"panel.html {len(html)/1024:.0f} KB -> {out}")
