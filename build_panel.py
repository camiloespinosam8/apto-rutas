# build_panel.py — Genera panel.html (dashboard 5 pestañas) leyendo datos.json precomputado.
import json, os, sys
from datetime import date
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = os.path.dirname(os.path.abspath(__file__))
D = json.load(open(os.path.join(HERE, "datos.json"), encoding="utf-8"))

DIAS = ["lunes","martes","miércoles","jueves","viernes","sábado","domingo"]
MESES = ["enero","febrero","marzo","abril","mayo","junio","julio","agosto","septiembre","octubre","noviembre","diciembre"]
h = date.fromisoformat(D["generado"])
FECHA_TXT = f"{DIAS[h.weekday()]} {h.day} de {MESES[h.month-1]} de {h.year}"

CSS = """
:root{--bg:#f4f6f8;--card:#fff;--tx:#15181c;--mut:#6b7280;--line:#e3e6ea;--acc:#2563eb;--in:#16a34a;--out:#ea8a1e;--st:#2563eb;--qr:#9333ea;--red:#dc2626;--amb:#d97706;--gr:#059669}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,'Segoe UI',Roboto,sans-serif;background:var(--bg);color:var(--tx);-webkit-font-smoothing:antialiased;padding:14px;max-width:1100px;margin:0 auto}
h1{font-size:1.3rem;font-weight:800;letter-spacing:-.02em}
.sub{color:var(--mut);font-size:.82rem;margin-top:2px;text-transform:capitalize}
.tabs{display:flex;gap:6px;margin:14px 0 16px;overflow-x:auto;padding-bottom:4px;-webkit-overflow-scrolling:touch}
.tab{white-space:nowrap;border:1.5px solid var(--line);background:var(--card);color:var(--tx);font-weight:700;font-size:.82rem;padding:8px 14px;border-radius:22px;cursor:pointer;transition:.15s}
.tab.active{background:var(--acc);color:#fff;border-color:var(--acc)}
.pane{display:none} .pane.on{display:block}
input,select{font:inherit;padding:9px 12px;border:1.5px solid var(--line);border-radius:10px;background:var(--card);color:var(--tx);width:100%}
input:focus,select:focus{outline:none;border-color:var(--acc)}
.row{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:12px}
.row>*{flex:1;min-width:140px}
.card{background:var(--card);border-radius:13px;padding:13px 15px;margin-bottom:9px;box-shadow:0 1px 3px rgba(0,0,0,.05)}
.pt{font-weight:800;font-size:1rem;display:flex;align-items:center;gap:7px;flex-wrap:wrap}
.chip{background:var(--line);color:var(--mut);font-size:.7rem;font-weight:700;padding:2px 8px;border-radius:10px}
.chip.st{background:var(--st);color:#fff}.chip.qr{background:var(--qr);color:#fff}
.chip.ok{background:#dcfce7;color:#166534}.chip.no{background:#fee2e2;color:#991b1b}
.kv{display:grid;grid-template-columns:118px 1fr;gap:3px 10px;margin-top:9px;font-size:.85rem}
.kv dt{color:var(--mut);font-weight:600}.kv dd{word-break:break-word}
details summary{cursor:pointer;color:var(--acc);font-size:.8rem;font-weight:700;margin-top:8px}
.ag{display:flex;gap:12px;align-items:center;border-left:4px solid transparent;padding-left:10px}
.ag.in{border-left-color:var(--in)}.ag.out{border-left-color:var(--out)}
.ag .hh{font-weight:800;min-width:52px;text-align:center}
.ag.in .hh{color:var(--in)}.ag.out .hh{color:var(--out)}
.dayhdr{font-weight:800;font-size:.78rem;text-transform:uppercase;letter-spacing:.05em;color:var(--mut);margin:16px 0 7px}
table{width:100%;border-collapse:collapse;font-size:.85rem;background:var(--card);border-radius:12px;overflow:hidden}
th{background:var(--line);text-align:left;padding:9px 10px;font-size:.72rem;text-transform:uppercase;letter-spacing:.04em;cursor:pointer;user-select:none;white-space:nowrap}
th:hover{color:var(--acc)} td{padding:9px 10px;border-top:1px solid var(--line)}
.bar{height:7px;background:var(--line);border-radius:5px;overflow:hidden;min-width:52px}
.bar>i{display:block;height:100%;background:var(--acc)}
.cal{overflow-x:auto;background:var(--card);border-radius:12px;padding:10px}
.calgrid{display:grid;gap:1px;min-width:760px}
.cell{height:24px;border-radius:3px;background:#e8f5e9}
.cell.busy{background:#ef5350}.cell.hdr{background:transparent;font-size:.6rem;color:var(--mut);text-align:center;height:auto;font-weight:700}
.calname{font-size:.72rem;font-weight:700;padding-right:8px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;line-height:24px}
.leg{display:flex;gap:14px;font-size:.75rem;color:var(--mut);margin:8px 0}
.leg i{display:inline-block;width:11px;height:11px;border-radius:3px;margin-right:4px;vertical-align:-1px}
.ex{display:flex;gap:6px;flex-wrap:wrap;margin:8px 0 12px}
.ex button{border:1.5px solid var(--acc);background:transparent;color:var(--acc);font-size:.76rem;font-weight:700;padding:6px 11px;border-radius:16px;cursor:pointer}
.ex button:hover{background:var(--acc);color:#fff}
.res{margin-top:10px}
.sev{font-size:.68rem;font-weight:800;padding:2px 8px;border-radius:10px;color:#fff}
.sev.alta{background:var(--red)}.sev.media{background:var(--amb)}.sev.baja{background:var(--gr)}
.catb{display:inline-block;font-size:.7rem;font-weight:800;padding:2px 9px;border-radius:10px;background:var(--line);color:var(--tx)}
.muted{color:var(--mut);font-size:.8rem}
.empty{color:var(--mut);font-style:italic;padding:14px;text-align:center}
footer{margin-top:24px;color:var(--mut);font-size:.72rem;text-align:center;border-top:1px solid var(--line);padding-top:12px}
@media(prefers-color-scheme:dark){:root{--bg:#0f1216;--card:#191d22;--tx:#e8eaed;--mut:#9aa0a6;--line:#282d34}
.cell{background:#1f3b26}.cell.busy{background:#b03535}.chip.ok{background:#14532d;color:#bbf7d0}.chip.no{background:#7f1d1d;color:#fecaca}}
"""

JS = r"""
const D = window.__D__;
const $ = s => document.querySelector(s);
const esc = s => String(s==null?'':s).replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]));
const nrm = s => String(s||'').normalize('NFD').replace(/[̀-ͯ]/g,'').toLowerCase();

// ---------- tabs ----------
document.querySelectorAll('.tab').forEach(b=>b.onclick=()=>{
  document.querySelectorAll('.tab').forEach(x=>x.classList.remove('active'));
  document.querySelectorAll('.pane').forEach(x=>x.classList.remove('on'));
  b.classList.add('active'); $('#p'+b.dataset.t).classList.add('on');
});

// ---------- 1. PROPIEDADES ----------
function propCard(p){
  const reg = p.region==='Santiago'?'st':'qr';
  const park = p.park.tiene ? `<span class="chip ok">🅿️ ${esc(p.park.num?('N°'+p.park.num):'sí')}</span>` : '<span class="chip no">sin estac.</span>';
  const rat = p.rating?`<span class="chip">⭐ ${p.rating} (${p.nresenas||0})</span>`:'';
  const kv = [
    ['Dirección', (p.direccion||'—') + (p.depto?(' · depto '+p.depto):'')],
    ['Comuna', p.comuna||'—'], ['Tipo / cap.', (p.tipo||'—')+' · '+(p.cap?p.cap+' personas':'cap. s/i')],
    ['Camas', p.camas||'—'], ['Dueño', p.dueno||'—'], ['Responsable', p.responsable||'—'],
    ['Clave edificio', p.acceso.edificio||'—'], ['Clave depto', p.acceso.depto||'—'],
    ['Estacionamiento', p.acceso.estacionamiento||p.park.detalle||'—'],
    ['WiFi', p.wifi.red?(p.wifi.red+' / '+p.wifi.clave):'—'],
    ['Limpieza', p.limpieza?('$'+Number(p.limpieza).toLocaleString('es-CL')):'—'],
    ['Comisión', p.comision||'—'], ['Toallas', (p.toallas_c||'?')+' cuerpo / '+(p.toallas_m||'?')+' mano'],
    ['Actualizado', p.salud||'—']
  ].map(([k,v])=>`<dt>${k}</dt><dd>${esc(v)}</dd>`).join('');
  return `<div class="card">
    <div class="pt">${esc(p.nombre)} <span class="chip ${reg}">${esc(p.region)}</span> ${rat} ${park}</div>
    <div class="muted" style="margin-top:3px">${esc(p.titulo||'')}</div>
    <dl class="kv">${kv}</dl>
    ${p.notas?`<details><summary>Ver notas</summary><div class="muted" style="margin-top:6px">${esc(p.notas)}</div></details>`:''}
    ${p.url?`<div style="margin-top:8px"><a href="${p.url}" target="_blank" style="color:var(--acc);font-size:.8rem;font-weight:700">Ver anuncio ↗</a></div>`:''}
  </div>`;
}
function renderProps(){
  const q=nrm($('#qprop').value), reg=$('#fregion').value, tipo=$('#ftipo').value;
  const out=D.props.filter(p=>{
    if(reg!=='all'&&p.region!==reg) return false;
    if(tipo!=='all'&&p.tipo!==tipo) return false;
    if(!q) return true;
    return nrm([p.nombre,p.titulo,p.direccion,p.comuna,p.dueno,p.interno,p.depto].join(' ')).includes(q);
  });
  $('#nprop').textContent=out.length;
  $('#listaprop').innerHTML = out.length?out.map(propCard).join(''):'<div class="empty">Sin resultados</div>';
}

// ---------- 2. AGENDA ----------
function renderAgenda(){
  const f=$('#fagenda').value, reg=$('#fagregion').value;
  const dias = f==='hoy' ? [D.semana[0]] : D.semana;
  let html='';
  dias.forEach(d=>{
    const items=D.agenda.filter(a=>a.fecha===d && (reg==='all'||a.region===reg));
    if(f==='hoy'||items.length){
      const dt=new Date(d+'T12:00:00');
      const nom=['domingo','lunes','martes','miércoles','jueves','viernes','sábado'][dt.getDay()];
      html+=`<div class="dayhdr">${nom} ${dt.getDate()}/${dt.getMonth()+1} — ${items.length} movimiento${items.length===1?'':'s'}</div>`;
      html+= items.length? items.map(a=>`<div class="card ag ${a.tipo}">
        <div class="hh">${esc(a.hora)}</div>
        <div style="flex:1;min-width:0">
          <div style="font-weight:700">${esc(a.direccion||a.pnombre)} <span class="chip">${esc(a.comuna||a.region)}</span></div>
          <div class="muted">${a.tipo==='in'?'🟢 llega':'🟠 sale'} ${esc(a.huesped)}${a.pax?' · '+a.pax+'p':''} · ${esc(a.pnombre)}</div>
        </div></div>`).join('') : '<div class="empty">Sin movimientos</div>';
    }
  });
  $('#listaag').innerHTML=html||'<div class="empty">Sin movimientos</div>';
}

// ---------- 3. CALENDARIO + BUSCADOR INTELIGENTE ----------
const DIASCAL=45;
function fechas(n){const a=[],d=new Date(D.ventana.desde+'T12:00:00');for(let i=0;i<n;i++){a.push(d.toISOString().slice(0,10));d.setDate(d.getDate()+1);}return a;}
function renderCal(){
  const reg=$('#fcalregion').value;
  const ds=fechas(DIASCAL);
  const ps=D.props.filter(p=>reg==='all'||p.region===reg);
  let h=`<div class="calgrid" style="grid-template-columns:150px repeat(${DIASCAL},1fr)">`;
  h+='<div class="cell hdr"></div>'+ds.map(d=>{const t=new Date(d+'T12:00:00');return `<div class="cell hdr">${t.getDate()}</div>`}).join('');
  ps.forEach(p=>{
    h+=`<div class="calname" title="${esc(p.nombre)}">${esc(p.nombre)}</div>`;
    h+=ds.map(d=>{const o=(D.ocup[p.id]||{})[d];
      return `<div class="cell ${o?'busy':''}" title="${esc(p.nombre)} · ${d}${o?' · ocupado '+esc(o.h):' · LIBRE'}"></div>`}).join('');
  });
  $('#calgrid').innerHTML=h+'</div>';
}
// motor de consultas: precomputado, responde al instante
function libres(desde,hasta,pax,reg,park){
  const out=[];const d0=new Date(desde+'T12:00:00'),d1=new Date(hasta+'T12:00:00');
  D.props.forEach(p=>{
    if(reg&&reg!=='all'&&p.region!==reg) return;
    if(pax&&(!p.cap||p.cap<pax)) return;
    if(park&&!p.park.tiene) return;
    let ok=true;const d=new Date(d0);
    while(d<d1){const s=d.toISOString().slice(0,10); if((D.ocup[p.id]||{})[s]){ok=false;break;} d.setDate(d.getDate()+1);}
    if(ok) out.push(p);
  });
  return out;
}
function correr(){
  const desde=$('#qdesde').value,hasta=$('#qhasta').value;
  if(!desde||!hasta){$('#qres').innerHTML='<div class="empty">Elige fechas</div>';return;}
  const pax=parseInt($('#qpax').value)||0, reg=$('#qregion').value, park=$('#qpark').checked;
  const r=libres(desde,hasta,pax,reg,park);
  const noches=Math.round((new Date(hasta)-new Date(desde))/864e5);
  $('#qres').innerHTML=`<div class="dayhdr">${r.length} libre${r.length===1?'':'s'} · ${desde} → ${hasta} (${noches} noche${noches===1?'':'s'})${pax?' · '+pax+'+ personas':''}${park?' · con estacionamiento':''}</div>`+
    (r.length?r.map(p=>`<div class="card"><div class="pt">${esc(p.nombre)} <span class="chip ${p.region==='Santiago'?'st':'qr'}">${esc(p.region)}</span>${p.cap?`<span class="chip">👥 ${p.cap}</span>`:''}${p.park.tiene?'<span class="chip ok">🅿️</span>':''}</div>
      <div class="muted" style="margin-top:3px">${esc(p.direccion||'')} ${esc(p.comuna||'')}</div></div>`).join('')
     :'<div class="empty">Nada libre con esos filtros</div>');
}
function preset(dd,nn,pax,park){
  const d=new Date(D.ventana.desde+'T12:00:00');d.setDate(d.getDate()+dd);
  const f=new Date(d);f.setDate(f.getDate()+nn);
  $('#qdesde').value=d.toISOString().slice(0,10);$('#qhasta').value=f.toISOString().slice(0,10);
  $('#qpax').value=pax||'';$('#qpark').checked=!!park;correr();
}

// ---------- 4. INSIGHTS ----------
let sortK='rating',sortD=-1;
function renderIns(){
  const reg=$('#finsregion').value;
  let rows=D.insights.filter(i=>reg==='all'||i.region===reg);
  rows.sort((a,b)=>{let x=a[sortK],y=b[sortK];
    if(x==null)x=-1;if(y==null)y=-1;
    if(typeof x==='string')return sortD*x.localeCompare(y);
    return sortD*(x-y);});
  $('#tbody').innerHTML=rows.map((i,n)=>`<tr>
    <td>${n+1}</td>
    <td><b>${esc(i.nombre)}</b><div class="muted">${esc(i.comuna||i.region)}</div></td>
    <td>${i.rating?('⭐ '+i.rating):'—'}</td>
    <td>${i.nresenas!=null?i.nresenas:'—'}</td>
    <td>${i.cap||'—'}</td>
    <td><div style="display:flex;align-items:center;gap:6px"><div class="bar"><i style="width:${i.ocup_pct}%"></i></div><span>${i.ocup_pct}%</span></div></td>
    <td>${i.limpieza?('$'+Number(i.limpieza).toLocaleString('es-CL')):'—'}</td></tr>`).join('');
}
document.querySelectorAll('th[data-k]').forEach(t=>t.onclick=()=>{
  const k=t.dataset.k; sortD = (sortK===k)? -sortD : -1; sortK=k; renderIns();});

// ---------- 5. INCIDENCIAS ----------
const CATN={insumos:'🧺 Insumos',higiene:'🧼 Higiene',tecnico:'🔧 Técnico',acceso:'🔑 Acceso / indicaciones'};
function renderInc(){
  const c=$('#fcat').value;
  const rows=D.incidencias.filter(i=>c==='all'||i.cat===c);
  const cnt={};D.incidencias.forEach(i=>cnt[i.cat]=(cnt[i.cat]||0)+1);
  $('#incres').innerHTML=Object.keys(CATN).map(k=>`<span class="chip">${CATN[k]}: <b>${cnt[k]||0}</b></span>`).join(' ');
  $('#listainc').innerHTML=rows.length?rows.map(i=>`<div class="card">
    <div class="pt"><span class="catb">${CATN[i.cat]||i.cat}</span> <span class="sev ${i.sev}">${i.sev}</span></div>
    <div style="font-weight:700;margin-top:7px">${esc(i.titulo)}</div>
    <div class="muted" style="margin-top:3px">${esc(i.prop)} · ${esc(i.fecha)}${i.huesped&&i.huesped!=='—'?' · '+esc(i.huesped):''}</div>
    <div style="margin-top:7px;font-size:.87rem">${esc(i.detalle)}</div>
    <div style="margin-top:7px;font-size:.85rem"><b>→ Acción:</b> ${esc(i.accion)}</div>
  </div>`).join(''):'<div class="empty">Sin incidencias en esta categoría</div>';
}

['qprop','fregion','ftipo'].forEach(id=>$('#'+id).addEventListener('input',renderProps));
['fagenda','fagregion'].forEach(id=>$('#'+id).addEventListener('input',renderAgenda));
$('#fcalregion').addEventListener('input',renderCal);
$('#finsregion').addEventListener('input',renderIns);
$('#fcat').addEventListener('input',renderInc);
$('#qgo').onclick=correr;
document.querySelectorAll('.ex button').forEach(b=>b.onclick=()=>preset(+b.dataset.d,+b.dataset.n,+b.dataset.p,b.dataset.k==='1'));
renderProps();renderAgenda();renderCal();renderIns();renderInc();
$('#qdesde').value=D.ventana.desde;
const t=new Date(D.ventana.desde+'T12:00:00');t.setDate(t.getDate()+2);$('#qhasta').value=t.toISOString().slice(0,10);
correr();
"""

tipos = sorted({p["tipo"] for p in D["props"] if p.get("tipo")})
opt_tipos = "".join(f'<option value="{t}">{t}</option>' for t in tipos)

html = f"""<!doctype html><html lang="es"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Centro de control APTO</title>
<style>{CSS}</style></head><body>
<header>
  <h1>🏢 Centro de control · APTO</h1>
  <div class="sub">{FECHA_TXT} · {len(D['props'])} propiedades · datos precalculados</div>
</header>

<div class="tabs">
  <button class="tab active" data-t="1">🏠 Propiedades</button>
  <button class="tab" data-t="2">📅 Check-in / out</button>
  <button class="tab" data-t="3">🗓️ Calendario y disponibilidad</button>
  <button class="tab" data-t="4">📊 Insights</button>
  <button class="tab" data-t="5">⚠️ Incidencias</button>
</div>

<div class="pane on" id="p1">
  <div class="row">
    <input id="qprop" placeholder="🔍 Buscar por nombre, dirección, comuna, dueño, depto…" style="flex:3">
    <select id="fregion"><option value="all">Todas las regiones</option><option>Santiago</option><option>Quinta Región</option></select>
    <select id="ftipo"><option value="all">Todos los tipos</option>{opt_tipos}</select>
  </div>
  <div class="muted"><b id="nprop">0</b> propiedades</div>
  <div id="listaprop" style="margin-top:10px"></div>
</div>

<div class="pane" id="p2">
  <div class="row">
    <select id="fagenda"><option value="hoy">Solo hoy</option><option value="semana">Toda la semana (7 días)</option></select>
    <select id="fagregion"><option value="all">Todas las regiones</option><option>Santiago</option><option>Quinta Región</option></select>
  </div>
  <div id="listaag"></div>
</div>

<div class="pane" id="p3">
  <div class="dayhdr">Consulta rápida — respuesta instantánea</div>
  <div class="ex">
    <button data-d="0" data-n="1" data-p="0" data-k="0">Libre hoy</button>
    <button data-d="1" data-n="1" data-p="0" data-k="0">Libre mañana</button>
    <button data-d="0" data-n="2" data-p="4" data-k="0">4 personas, 2 noches</button>
    <button data-d="0" data-n="2" data-p="4" data-k="1">4 pers. + estacionamiento</button>
    <button data-d="0" data-n="3" data-p="6" data-k="0">6 personas, 3 noches</button>
    <button data-d="0" data-n="7" data-p="8" data-k="0">8 personas, 1 semana</button>
  </div>
  <div class="row">
    <input type="date" id="qdesde"><input type="date" id="qhasta">
    <input type="number" id="qpax" placeholder="N° personas" min="1">
    <select id="qregion"><option value="all">Todas</option><option>Santiago</option><option>Quinta Región</option></select>
    <label style="display:flex;align-items:center;gap:6px;font-size:.85rem;flex:0 0 auto"><input type="checkbox" id="qpark" style="width:auto"> 🅿️ estac.</label>
    <button id="qgo" class="tab active" style="flex:0 0 auto">Buscar</button>
  </div>
  <div id="qres" class="res"></div>
  <div class="dayhdr" style="margin-top:22px">Calendario de ocupación (45 días)</div>
  <div class="row"><select id="fcalregion" style="max-width:220px"><option value="all">Todas las regiones</option><option>Santiago</option><option>Quinta Región</option></select></div>
  <div class="leg"><span><i style="background:#e8f5e9"></i>Libre</span><span><i style="background:#ef5350"></i>Ocupado</span></div>
  <div class="cal"><div id="calgrid"></div></div>
</div>

<div class="pane" id="p4">
  <div class="row"><select id="finsregion" style="max-width:220px"><option value="all">Todas las regiones</option><option>Santiago</option><option>Quinta Región</option></select></div>
  <div class="muted" style="margin-bottom:8px">Clic en los títulos para ordenar</div>
  <table><thead><tr>
    <th>#</th><th data-k="nombre">Propiedad</th><th data-k="rating">Rating</th><th data-k="nresenas">Reseñas</th>
    <th data-k="cap">Cap.</th><th data-k="ocup_pct">Ocupación</th><th data-k="limpieza">Limpieza</th>
  </tr></thead><tbody id="tbody"></tbody></table>
</div>

<div class="pane" id="p5">
  <div class="row"><select id="fcat" style="max-width:260px">
    <option value="all">Todas las categorías</option>
    <option value="insumos">🧺 Insumos</option>
    <option value="higiene">🧼 Problemas higiénicos</option>
    <option value="tecnico">🔧 Problemas técnicos</option>
    <option value="acceso">🔑 Acceso / indicaciones</option>
  </select></div>
  <div id="incres" style="margin-bottom:10px"></div>
  <div id="listainc"></div>
</div>

<footer>APTO · centro de control — se actualiza solo cada día · datos precalculados para respuesta inmediata</footer>
<script>window.__D__={json.dumps(D, ensure_ascii=False, separators=(',',':'))};</script>
<script>{JS}</script>
</body></html>"""

out = os.path.join(HERE, "panel.html")
open(out, "w", encoding="utf-8").write(html)
print(f"panel.html {len(html)/1024:.0f} KB -> {out}")
