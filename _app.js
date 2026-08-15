
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
