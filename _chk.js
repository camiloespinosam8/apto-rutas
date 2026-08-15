
const D=window.__D__, $=s=>document.querySelector(s);
const esc=s=>String(s==null?'':s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const nrm=s=>String(s||'').normalize('NFD').replace(/\p{Diacritic}/gu,'').toLowerCase();
const clp=n=>{const v=Number(n);return Number.isFinite(v)&&v>0?('$'+v.toLocaleString('es-CL')):''};
const VAC=new Set(['','-','—','s/n','sn','casa','none','null','?']);
const ok=v=>{const s=String(v==null?'':v).trim();return VAC.has(s.toLowerCase())?'':s};

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
function irA(t){
  const b=document.querySelector('.tab[data-t="'+t+'"]'); if(b){b.click();window.scrollTo({top:0,behavior:'smooth'});}
}
// ---- tabs ----
document.querySelectorAll('.tab').forEach(b=>b.onclick=()=>{
  document.querySelectorAll('.tab').forEach(x=>x.setAttribute('aria-selected','false'));
  document.querySelectorAll('.pane').forEach(x=>x.classList.remove('on'));
  b.setAttribute('aria-selected','true'); $('#p'+b.dataset.t).classList.add('on');
});

/* ============ MOTOR DE CONSULTA · precomputado, responde al instante ============
   Entiende: fechas sueltas y rangos en español, nº de personas, estacionamiento,
   región/comuna, tipo, códigos de reserva, nombres, e INTENCIÓN de la pregunta.      */
const MES={ene:1,enero:1,feb:2,febrero:2,mar:3,marzo:3,abr:4,abril:4,may:5,mayo:5,
  jun:6,junio:6,jul:7,julio:7,ago:8,agosto:8,sep:9,sept:9,set:9,septiembre:9,
  oct:10,octubre:10,nov:11,noviembre:11,dic:12,diciembre:12};
const iso=d=>d.toISOString().slice(0,10);
function base(){return new Date(D.ventana.desde+'T12:00:00')}
const masDias=(d,n)=>{const x=new Date(d);x.setDate(x.getDate()+n);return x};
function armar(dia,mes){const d=base();if(mes)d.setMonth(mes-1,dia);else d.setDate(dia);
  if(d<base())d.setFullYear(d.getFullYear()+(mes?1:0));return d}

/* ---- rango de fechas: devuelve {desde,hasta,noches} o null ---- */
function parseRango(s){
  const M='(ene|enero|feb|febrero|mar|marzo|abr|abril|may|mayo|jun|junio|jul|julio|ago|agosto|sep|sept|set|septiembre|oct|octubre|nov|noviembre|dic|diciembre)';
  let m;
  // "del 20 al 25 de agosto" | "20 al 25 ago" | "20-25 ago"
  m=s.match(new RegExp('\\b(\\d{1,2})\\s*(?:al|a|-|hasta)\\s*(\\d{1,2})\\s*(?:de\\s*)?'+M));
  if(m){const mm=MES[m[3]];return rango(armar(+m[1],mm),armar(+m[2],mm))}
  // "20/8 al 25/8"
  m=s.match(/\b(\d{1,2})[\/-](\d{1,2})\s*(?:al|a|-|hasta)\s*(\d{1,2})[\/-](\d{1,2})\b/);
  if(m)return rango(armar(+m[1],+m[2]),armar(+m[3],+m[4]));
  // "3 noches desde el 20 (de ago)"
  m=s.match(new RegExp('(\\d{1,2})\\s*noches?.*?\\b(\\d{1,2})\\s*(?:de\\s*)?'+M+'?'));
  if(m){const d0=armar(+m[2],MES[m[3]]);return rango(d0,masDias(d0,+m[1]))}
  // relativas
  if(/\beste (finde|fin de semana)\b|\bfinde\b/.test(s)){
    const d=base(),dow=d.getDay(),sab=masDias(d,(6-dow+7)%7);return rango(sab,masDias(sab,2));}
  if(/\bproxima semana\b|\bsemana que viene\b/.test(s)){
    const d=base(),lun=masDias(d,((8-d.getDay())%7)||7);return rango(lun,masDias(lun,7));}
  if(/\besta semana\b/.test(s))return rango(base(),masDias(base(),7));
  if(/\beste mes\b/.test(s))return rango(base(),masDias(base(),30));
  const f=parseFecha(s); if(f){const d=new Date(f+'T12:00:00');return rango(d,masDias(d,1))}
  return null;
}
function rango(a,b){if(b<=a)b=masDias(a,1);
  return {desde:iso(a),hasta:iso(b),noches:Math.round((b-a)/864e5)}}
function parseFecha(s){
  if(/\bhoy\b/.test(s))return D.ventana.desde;
  if(/\bmanana\b/.test(s))return iso(masDias(base(),1));
  if(/\bpasado manana\b/.test(s))return iso(masDias(base(),2));
  let m=s.match(/(\d{4})-(\d{2})-(\d{2})/); if(m)return m[0];
  m=s.match(/\b(\d{1,2})[\/-](\d{1,2})\b/);            if(m)return iso(armar(+m[1],+m[2]));
  // recorrer TODOS los "<n> <palabra>": quedarse con el primero cuya palabra sea un mes real
  // (si no, "4 personas 20 de agosto" tomaría "4 personas" como fecha y perdería el 20 de agosto)
  for(const mm of s.matchAll(/\b(\d{1,2})\s*(?:de\s*)?([a-z]{3,10})\b/g))
    if(MES[mm[2]])return iso(armar(+mm[1],MES[mm[2]]));
  return null;
}
function parsePax(s){
  let m=s.match(/(\d{1,2})\s*(?:p\b|pax|persona|huesped|adulto|pasajero)/); if(m)return +m[1];
  m=s.match(/\bpara\s+(\d{1,2})\b/);      if(m)return +m[1];
  m=s.match(/\bgrupo de\s+(\d{1,2})\b/);  if(m)return +m[1];
  return 0;
}
const pidePark=s=>/\bpark\w*|\bestacion\w*|\bauto\b|\bautos\b|\bcochera\b/.test(s);
function pideRegion(s){
  if(/\bvalpo\b|\bvalparaiso\b|\bvina\b|\bconcon\b|\bquinta\b|\bcosta\b/.test(s))return 'Quinta Región';
  if(/\bsantiago\b|\bstgo\b|\brm\b/.test(s))return 'Santiago';
  return 'all';
}
function pideComuna(s){
  for(const c of ['nunoa','providencia','las condes','santiago centro','valparaiso','vina del mar','concon'])
    if(s.includes(c))return c;
  return '';
}
function pideTipo(s){
  if(/\bcasas?\b/.test(s))return 'casa';
  if(/\bstudios?\b/.test(s))return 'studio';
  if(/\b(\dd)\b/.test(s))return s.match(/\b(\dd)\b/)[1].toUpperCase();
  if(/\bdeptos?\b|\bdepartamentos?\b|\bapart\w*/.test(s))return 'depto';
  return '';
}
/* ---- intención: qué está preguntando ---- */
function intencion(s){
  if(/\blibre\b|\bdisponib\w*|\bqueda algo\b|\bhay algo\b|\btengo algo\b|\bofrecer\b|\bvac[ií]o\b/.test(s))return 'disp';
  if(/\bllega\b|\bllegan\b|\bentra\b|\bsale\b|\bsalen\b|\bcheck ?in\b|\bcheck ?out\b|\bmovimiento\b|\bquien\b/.test(s))return 'mov';
  if(/\bproblema\w*|\bfalla\w*|\breclamo\b|\burgent\w*|\bincidencia\w*|\bqueja\w*|\bsin \w+/.test(s))return 'inc';
  if(/\bclave\b|\bcodigo\b|\bwifi\b|\bdireccion\b|\bdonde\b|\bacceso\b|\bllave\b/.test(s))return 'prop';
  return '';
}
const RE_COD=/\bhm[a-z0-9]{8}\b/i;
function parseQuery(q){
  const s=nrm(q);
  return {q, s, rango:parseRango(s), pax:parsePax(s), park:pidePark(s),
    region:pideRegion(s), comuna:pideComuna(s), tipo:pideTipo(s),
    intent:intencion(s), cod:(s.match(RE_COD)||[''])[0].toUpperCase()};
}
function libres(de,ha,pax,reg,pk,com,tipo){
  const out=[],d0=new Date(de+'T12:00:00'),d1=new Date(ha+'T12:00:00');
  D.props.forEach(p=>{
    if(reg&&reg!=='all'&&p.region!==reg)return;
    if(pax&&(!p.cap||p.cap<pax))return;
    if(pk&&!(p.park&&p.park.tiene))return;
    if(com&&!nrm(p.comuna).includes(com))return;
    if(tipo){const t=nrm(p.tipo);
      if(tipo==='casa'&&!t.includes('casa'))return;
      if(tipo==='depto'&&(t.includes('casa')||!t))return;
      if(tipo==='studio'&&!t.includes('studio'))return;
      if(/^\dD$/.test(tipo)&&t!==nrm(tipo))return;}
    let libre=true;const d=new Date(d0);
    while(d<d1){if((D.ocup[p.id]||{})[iso(d)]){libre=false;break}d.setDate(d.getDate()+1)}
    if(libre)out.push(p);
  });
  return out;
}
/* ---- contacto y contexto de una urgencia ---- */
const soloNum=t=>String(t||'').replace(/\D/g,'');
function waLink(t){const n=soloNum(t);return n.length>=8?'https://wa.me/'+n:''}
const resLink=c=>c?('https://www.airbnb.cl/hosting/reservations/details/'+c):'';
function propDe(i){
  const pi=nrm(i.prop); if(!pi)return null;
  return D.props.find(p=>[ok(p.calle),ok(p.nombre),ok(p.interno)]
    .some(k=>k&&String(k).length>3&&pi.includes(nrm(k))))||null;
}
/* QUIÉN REPORTÓ vs QUIÉN ESTÁ AHORA — son cosas distintas y no deben mezclarse.
   Antes, si la incidencia no traía código, se le asignaba la reserva alojada hoy: eso
   atribuía un problema de un huésped ANTERIOR al huésped ACTUAL (y ofrecía escribirle).
   Ahora: solo se identifica al reportante cuando la incidencia trae su código. */
function reservaDe(i){
  return (i.cod && D.res_ix[i.cod]) ? {cod:i.cod, ...D.res_ix[i.cod]} : null;
}
// Contexto de propiedad (NO es quien reportó): quién ocupa la propiedad hoy.
function ocupanteHoy(i){
  const p=propDe(i); if(!p)return null;
  const c=D.estadia[p.id];
  return c&&D.res_ix[c]?{cod:c,...D.res_ix[c]}:null;
}
const dmy=f=>{const d=new Date(f+'T12:00:00');
  return d.getDate()+' '+['ene','feb','mar','abr','may','jun','jul','ago','sep','oct','nov','dic'][d.getMonth()]};
/* ---- casuística: en qué momento del viaje está el huésped que reclamó ---- */
const HORA_CI = 15;   // check-in estándar
function casuistica(i){
  const r=reservaDe(i); const hoy=D.ventana.desde;
  if(!r) return {k:'sin', r:null};
  if(r.e>hoy)   return {k:'pre', r};                                   // aún no llega
  if(r.e===hoy) return {k:(new Date().getHours()<HORA_CI?'manana':'durante'), r};
  if(r.s<=hoy)  return {k:'post', r};                                  // ya se fue
  return {k:'estadia', r};                                             // lleva noches
}

/* Contacto SOLO al que reportó. "Ya se fue" => sin botón (no se molesta a quien ya no está).
   Si no se sabe quién reportó, no se inventa: se muestra solo quién ocupa hoy, como contexto. */
function contactoHTML(i,sinContacto){
  const r=reservaDe(i);
  if(!r){
    const o=ocupanteHoy(i);
    if(!o)return '';
    return `<div class="ctc"><span class="tg" style="color:var(--vino)">no se sabe quién lo reportó</span>
      <span class="tg">ocupa hoy: ${esc(o.h)} hasta ${dmy(o.s)}</span>
      <a class="lk" href="${resLink(o.cod)}" target="_blank" rel="noopener">Ver reserva actual ↗</a></div>`;
  }
  const hoy=D.ventana.desde, seFue=r.s<=hoy;
  const t=D.tel[r.cod]||'', wa=waLink(t);
  const cual=seFue?'estuvo':(r.e<=hoy&&r.s>hoy?'alojado':'reserva');
  const bits=[`<span class="tg" style="color:var(--tinta)">${esc(r.h)}</span>`,
              `<span class="tg">${cual} ${dmy(r.e)} → ${dmy(r.s)}</span>`];
  const links=[];
  if(wa&&!sinContacto&&!seFue)links.push(`<a class="lk wa" href="${wa}" target="_blank" rel="noopener">Contactar</a>`);
  links.push(`<a class="lk" href="${resLink(r.cod)}" target="_blank" rel="noopener">Reserva ${esc(r.cod)} ↗</a>`);
  // si el que reportó ya se fue pero hay otro adentro, avisarlo: el problema puede seguir vivo
  const o=seFue?ocupanteHoy(i):null;
  const extra=o?`<span class="tg" style="color:var(--vino)">ahora ocupa ${esc(o.h)} hasta ${dmy(o.s)}</span>`:'';
  return `<div class="ctc">${bits.join(' ')} ${extra} ${links.join(' ')}</div>`;
}
const txtProp=p=>[p.nombre,p.calle,p.numero,p.depto,p.comuna,p.interno,p.dueno,p.responsable,p.tipo].join(' ');
const txtMov =a=>[a.dir,a.pnombre,a.huesped,a.comuna,a.cod].join(' ');
const txtInc =i=>[i.titulo,i.prop,i.detalle,i.cat,i.cita,i.huesped,i.cod].join(' ');

/* ---- carencias: qué le FALTA al huésped (lo que hay que resolver hoy) ---- */
// \b en ambos extremos: "gas" NO debe matchear "descargas". Orden = prioridad operativa.
const CARENCIA=[
  [/\bfuga de gas\b|\bsin gas\b|\bbalon de gas\b|\bgas\b/,'sin gas',0],
  [/\bagua caliente\b|\bno calienta\b|\bcalefon\b|\btermo\b|\bagua helada\b/,'sin agua caliente',1],
  [/\bsin agua\b|\bno hay agua\b|\bcorte de agua\b/,'sin agua',1],
  [/\belectric\w*|\bsin luz\b|\bdisyuntor\w*|\bbreaker\w*|\benchufe\w*/,'sin luz',2],
  [/\bno pudo (entrar|ingresar)\b|\bconserjer\w*|\bclave\b|\bcodigo\b|\bchapa\b|\bautorizacion\b|\bno funciono la contrasena\b/,'sin acceso',2],
  [/\bcalefacc\w*|\bcalefactor\w*|\bestufa\w*|\bmucho frio\b|\bsin frazada\b/,'sin calefacción',3],
  [/\bwifi\b|\binternet\b/,'sin internet',4],
  [/\btoalla\w*|\bsabana\w*|\bropa de cama\b|\bedredon\w*|\bcobertor\w*|\bfrazada\w*/,'sin toallas/ropa',4],
  [/\binodoro\b|\bsuelt[oa]\b|\bquebrad[oa]\b|\brot[oa]\b|\bse cayo\b|\bdanad[oa]\b/,'algo roto',3],
  [/\blimpieza\b|\bsucia?o?\b|\bmancha\w*|\baseo\b/,'aseo',5],
  [/\bcafetera\b|\bplancha\b|\bsecador\b|\butensilio\w*/,'falta insumo',6],
];
// Solo TÍTULO y CITA del huésped. El detalle menciona otros temas de pasada y ensucia la etiqueta;
// preferimos no etiquetar (y mostrar la categoría) antes que etiquetar mal.
function carencia(i){
  for(const campo of [i.titulo, (i.titulo||'')+' '+(i.cita||'')]){
    const b=nrm(campo);
    if(!b) continue;
    for(const [re,txt,ord] of CARENCIA) if(re.test(b)) return {txt,ord};
  }
  return null;
}
// ¿hay alguien alojado HOY en la propiedad de esta incidencia?
function conHuespedHoy(i){
  const hoy=D.ventana.desde, pi=nrm(i.prop);
  if(!pi) return false;
  return D.props.some(p=>{
    if(!(D.ocup[p.id]||{})[hoy]) return false;
    const claves=[ok(p.calle),ok(p.nombre),ok(p.interno),ok(p.depto)].filter(x=>x&&String(x).length>3).map(nrm);
    return claves.some(k=>pi.includes(k));
  });
}
function urgentesHoy(n){
  const cand=D.incidencias.filter(i=>i.estado!=='resuelto').map(i=>{
    const c=carencia(i);
    return {...i, _c:c?c.txt:null, _o:c?c.ord:9, _hoy:conHuespedHoy(i)};
  }).filter(i=>i._c||i.sev==='alta');
  cand.sort((a,b)=>(b._hoy-a._hoy)||(a._o-b._o)||
    ((a.sev==='alta'?0:a.sev==='media'?1:2)-(b.sev==='alta'?0:b.sev==='media'?1:2)));
  return cand.slice(0,n);
}

/* ---- fila de incidencia (compartida por HOME, buscador y pestaña) ---- */
const CATN={insumos:'Insumos',higiene:'Higiene',tecnico:'Técnico',acceso:'Acceso',otros:'Otros'};
function filaInc(i,compacto,sinContacto){
  const c=carencia(i), et=c?c.txt:(CATN[i.cat]||i.cat);
  return `<div class="r">
    <div class="t ${i.sev==='alta'?'out':'in'} etq">${esc(et)}</div>
    <div class="m"><div class="n">${esc(i.titulo)}</div>
      <div class="d">${esc(i.prop)}${i.huesped?' · '+esc(i.huesped):''}${compacto?'':' · '+esc(i.fecha)}</div>
      ${i.cita?`<div class="d" style="font-style:italic">«${esc(i.cita)}»</div>`:''}
      ${contactoHTML(i,sinContacto)}
      ${compacto?'':`<div class="acc"><b>→</b> ${esc(i.accion)}</div>`}</div>
    <div class="tags"><span class="sev ${i.sev}">${esc(i.sev)}</span>
      ${compacto?'':`<span class="tg" style="color:${i.estado==='resuelto'?'var(--exito)':'var(--vino)'}">${esc(i.estado)}</span>`}</div></div>`;
}

/* ============ HOME ============ */
function pintarHome(){
  const hoy=D.ventana.desde;
  const ins=D.agenda.filter(a=>a.fecha===hoy&&a.tipo==='in').length;
  const outs=D.agenda.filter(a=>a.fecha===hoy&&a.tipo==='out').length;
  const man=iso(new Date(new Date(hoy+'T12:00:00').getTime()+864e5));
  const libHoy=libres(hoy,man,0,'all',false).length;
  const abiertas=D.incidencias.filter(i=>i.estado!=='resuelto').length;
  $('#pulse').innerHTML=
    `<div class="pz i"><b>${ins}</b><span>llegan hoy</span></div>
     <div class="pz o"><b>${outs}</b><span>salen hoy</span></div>
     <div class="pz l"><b>${libHoy}</b><span>libres hoy</span></div>
     <div class="pz"><b>${abiertas}</b><span>sin resolver</span></div>`;
  // ---- 0. conserjería te escribió y nadie contestó ----
  const resp=(D.acc_resp||[]);
  $('#resp').innerHTML=resp.length?`<div class="gsec">Conserjería espera respuesta <span class="cnt">${resp.length}</span></div>
    <div class="rows">`+resp.map(r=>`<div class="r">
      <div class="t out etq">responder</div>
      <div class="m"><div class="n">«${esc(r.texto)}»</div>
        <div class="d">${esc(r.de)} · ${esc(r.fecha)} · ${esc(r.prop)}</div>
        ${r.cod?`<div class="ctc"><a class="lk" href="${resLink(r.cod)}" target="_blank" rel="noopener">Reserva ${esc(r.cod)} ↗</a></div>`:''}</div>
      <div class="tags"><span class="sev ${r.urgencia}">${esc(r.urgencia)}</span></div></div>`).join('')+'</div>':'';

  // ---- 1. reserva confirmada SIN el correo de acceso enviado ----
  const ac=(D.accesos_pend||[]);
  const acHoy=ac.filter(a=>a.hoy);
  $('#acc').innerHTML=ac.length?`<div class="gsec">Acceso sin enviar a conserjería <span class="cnt">${ac.length}</span>
      ${acHoy.length?`<span class="alerta">${acHoy.length} llegan hoy</span>`:''}</div>
    <div class="rows">`+ac.slice(0,8).map(a=>`<div class="r">
      <div class="t ${a.hoy?'out':'in'} etq">${a.hoy?'llega HOY':dmy(a.entrada)}</div>
      <div class="m"><div class="n">${esc(a.dir||a.prop)}</div>
        <div class="d">${esc(a.huesped)}${a.pax?' · '+a.pax+'p':''} · entra ${esc(a.hin)}</div>
        <div class="ctc">${D.tel[a.cod]?`<a class="lk wa" href="${waLink(D.tel[a.cod])}" target="_blank" rel="noopener">Contactar</a>`:''}
          <a class="lk" href="${resLink(a.cod)}" target="_blank" rel="noopener">Reserva ${esc(a.cod)} ↗</a></div></div>
      </div>`).join('')+`</div>${D.acc_auditado?`<div class="hint">Correo revisado el ${esc(D.acc_auditado)}</div>`:''}`:'';

  // ---- 2/3/1: por casuística, en el orden que importa ----
  const pend=D.incidencias.filter(i=>i.estado!=='resuelto').map(i=>{
    const c=carencia(i), cs=casuistica(i);
    return {...i,_c:c?c.txt:null,_o:c?c.ord:9,_k:cs.k};
  }).filter(i=>i._c||i.sev==='alta');
  const ord=(a,b)=>(a._o-b._o)||((a.sev==='alta'?0:a.sev==='media'?1:2)-(b.sev==='alta'?0:b.sev==='media'?1:2));
  const GRUPOS=[
    ['pre','Pre check-in','Aún no llega y ya hay algo que resolver antes de que entre.',false,4],
    ['manana','Mañana del check-in','Llega hoy en la tarde: queda la mañana para dejarlo resuelto.',false,4],
    ['durante','Durante el check-in','Está entrando ahora mismo con el problema encima.',false,4],
    ['estadia','Durante estadía','Lleva noches adentro y sigue sin resolverse.',false,5],
    ['post','Post check-out','Ya se fue: no se le escribe, se arregla antes del próximo.',true,4],
    ['sin','Sin reportante identificado','Fallas de fondo de barridos anteriores: se arreglan igual.',true,4],
  ];

  $('#urg').innerHTML=GRUPOS.map(([k,tit,sub,sinCt,n])=>{
    const g=pend.filter(i=>i._k===k).sort(ord).slice(0,n);
    if(!g.length)return '';
    return `<div class="gsec">${tit} <span class="cnt">${g.length}</span></div>
      <div class="hint">${sub}</div>
      <div class="rows">`+g.map(i=>filaInc(i,false,sinCt)).join('')+'</div>';
  }).join('')||'<div class="none">Nada urgente abierto</div>';
}
// palabras que ya consumió el parser: no sirven para buscar por texto
const RUIDO=/\b(libre|libres|disponible|disponibles|hay|algo|queda|tengo|para|con|sin|el|la|los|las|de|del|al|un|una|que|casa|casas|depto|deptos|departamento|persona|personas|pax|noche|noches|hoy|manana|finde|semana|mes|estacionamiento|parking|auto|autos|quien|llega|llegan|sale|salen|entra|check|in|out|problema|problemas|urgente|urgentes)\b/g;
function textoLibre(Q){
  return Q.s.replace(RE_COD,' ').replace(/\d{1,4}([\/-]\d{1,4})?/g,' ')
    .replace(RUIDO,' ').replace(/\s+/g,' ').trim();
}
function bloque(t,tab,html,vacio){
  return `<div class="gsec">${t} <button class="jump" onclick="irA(${tab})">ver →</button></div>`+
    (html||`<div class="none">${vacio}</div>`);
}
function buscarGlobal(){
  const q=$('#hq').value.trim();
  if(!q){$('#hres').innerHTML='';$('#home-def').style.display='';return}
  $('#home-def').style.display='none';
  const Q=parseQuery(q), libre=textoLibre(Q);
  const sec=[];

  // 0) código de reserva → ficha directa
  if(Q.cod&&D.res_ix[Q.cod]){
    const r=D.res_ix[Q.cod], t=D.tel[Q.cod]||'', wa=waLink(t);
    sec.push({o:0,h:bloque(`Reserva ${esc(Q.cod)}`,2,`<div class="rows"><div class="r"><div class="m">
      <div class="n">${esc(r.p)}</div><div class="d">${esc(r.h)} · ${dmy(r.e)} → ${dmy(r.s)}${r.pax?' · '+r.pax+'p':''}</div>
      <div class="ctc">${wa?`<a class="lk wa" href="${wa}" target="_blank" rel="noopener">Contactar</a> `:''}
        <a class="lk" href="${resLink(Q.cod)}" target="_blank" rel="noopener">Abrir en Airbnb ↗</a></div>
      </div></div></div>`,'')});
  }
  // 1) disponibilidad — si hay fecha, pax, parking, tipo o intención explícita
  if(Q.rango||Q.pax||Q.park||Q.tipo||Q.intent==='disp'){
    const R=Q.rango||{desde:D.ventana.desde,hasta:iso(masDias(base(),1)),noches:1};
    const L=libres(R.desde,R.hasta,Q.pax,Q.region,Q.park,Q.comuna,Q.tipo);
    const et=[`${dmy(R.desde)} → ${dmy(R.hasta)}`,`${R.noches}n`];
    if(Q.pax)et.push(Q.pax+'p'); if(Q.park)et.push('con P');
    if(Q.tipo)et.push(Q.tipo); if(Q.region!=='all')et.push(Q.region);
    sec.push({o:Q.intent==='disp'?0:1,h:bloque(`${L.length} libres · ${et.join(' · ')}`,3,
      L.length?'<div class="rows">'+L.slice(0,14).map(p=>`<div class="r"><div class="m">
        <div class="n">${esc(p.nombre)}</div><div class="d">${esc(dir(p))}</div></div>
        <div class="tags">${tagsProp(p)}</div></div>`).join('')+'</div>':'','Nada libre con esos filtros')});
  }
  // 2) propiedades
  if(libre||Q.intent==='prop'){
    const P=D.props.filter(p=>!libre||nrm(txtProp(p)).includes(libre)).slice(0,8);
    if(P.length)sec.push({o:Q.intent==='prop'?0:2,h:bloque('Propiedades',1,
      '<div class="rows">'+P.map(p=>rowProp(p)).join('')+'</div>','')});
  }
  // 3) movimientos
  {
    let M=D.agenda.filter(a=>!libre||nrm(txtMov(a)).includes(libre));
    if(Q.rango)M=M.filter(a=>a.fecha>=Q.rango.desde&&a.fecha<=Q.rango.hasta);
    if(Q.region!=='all')M=M.filter(a=>a.region===Q.region);
    if((libre||Q.intent==='mov')&&M.length)sec.push({o:Q.intent==='mov'?0:3,h:bloque('Movimientos',2,
      '<div class="rows">'+M.slice(0,10).map(a=>`<div class="r"><div class="t ${a.tipo}">${esc(a.hora)}</div>
      <div class="m"><div class="n">${esc(a.dir||a.pnombre)}</div>
      <div class="d">${dmy(a.fecha)} · ${a.tipo==='in'?'entra':'sale'} ${esc(a.huesped)}${a.cod?' · '+esc(a.cod):''}</div>
      ${a.cod?`<div class="ctc">${D.tel[a.cod]?`<a class="lk wa" href="${waLink(D.tel[a.cod])}" target="_blank" rel="noopener">Contactar</a> `:''}<a class="lk" href="${resLink(a.cod)}" target="_blank" rel="noopener">Reserva ↗</a></div>`:''}
      </div></div>`).join('')+'</div>','')});
  }
  // 4) incidencias
  {
    const I=D.incidencias.filter(i=>(!libre||nrm(txtInc(i)).includes(libre))
      &&(Q.intent!=='inc'||i.estado!=='resuelto')).slice(0,8);
    if((libre||Q.intent==='inc')&&I.length)sec.push({o:Q.intent==='inc'?0:4,h:bloque('Incidencias',5,
      '<div class="rows">'+I.map(i=>filaInc(i,true)).join('')+'</div>','')});
  }
  sec.sort((a,b)=>a.o-b.o);
  $('#hres').innerHTML=sec.length?sec.map(x=>x.h).join(''):
    '<div class="none">Sin resultados para «'+esc(q)+'»</div>';
}

/* ============ 1 PROPIEDADES ============ */
function rowProp(p){
  const claves=[ok(p.acceso.depto)&&('depto '+ok(p.acceso.depto)),
                ok(p.acceso.edificio)&&('edificio '+ok(p.acceso.edificio))].filter(Boolean).join(' · ');
  const kv=[['Dirección',dir(p)],['Clave momentánea',claves],
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
  const o=D.props.filter(p=>(reg==='all'||p.region===reg)&&(!q||nrm(txtProp(p)).includes(q)));
  $('#np').textContent=o.length;
  $('#lp').innerHTML=o.length?o.map(rowProp).join(''):'<div class="none">Sin resultados</div>';
}
/* ============ 2 MOVIMIENTOS ============ */
function renderAg(){
  const f=$('#fa').value,reg=$('#far').value,q=nrm($('#qa').value);
  const dias=f==='hoy'?[D.semana[0]]:D.semana;
  let h='';
  dias.forEach(d=>{
    const it=D.agenda.filter(a=>a.fecha===d&&(reg==='all'||a.region===reg)&&(!q||nrm(txtMov(a)).includes(q)));
    if((f==='hoy'&&!q)||it.length){
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
/* ============ 3 DISPONIBILIDAD ============ */
const NC=45;
function fechas(n){const a=[],d=base();for(let i=0;i<n;i++){a.push(iso(d));d.setDate(d.getDate()+1)}return a}
function renderCal(){
  const reg=$('#fcr').value,q=nrm($('#qc').value),ds=fechas(NC);
  const ps=D.props.filter(p=>(reg==='all'||p.region===reg)&&(!q||nrm(txtProp(p)).includes(q)));
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
  const d=base();d.setDate(d.getDate()+dd);
  const f=new Date(d);f.setDate(f.getDate()+nn);
  $('#qd').value=iso(d);$('#qh').value=iso(f);
  $('#qx').value=pax||'';$('#qk').checked=!!pk;correr();
}
/* ============ 4 RANKING ============ */
let sk='rating',sd=-1;
function renderIns(){
  const reg=$('#fir').value,q=nrm($('#qi').value);
  const rows=D.insights.filter(i=>(reg==='all'||i.region===reg)&&
      (!q||nrm([i.nombre,i.comuna,i.tipo,i.dueno].join(' ')).includes(q)))
    .sort((a,b)=>{let x=a[sk],y=b[sk];if(x==null)x=-1;if(y==null)y=-1;
      return typeof x==='string'?sd*x.localeCompare(y):sd*(x-y)});
  $('#tb').innerHTML=rows.map((i,n)=>`<tr><td>${n+1}</td><td><b>${esc(i.nombre)}</b></td>
    <td>${Number(i.rating)>0?i.rating+'★':'—'}</td><td>${i.nresenas??'—'}</td><td>${i.cap||'—'}</td>
    <td><div style="display:flex;align-items:center;gap:7px"><div class="bar2"><i style="width:${i.ocup_pct}%"></i></div>${i.ocup_pct}%</div></td>
    <td>${clp(i.limpieza)||'—'}</td></tr>`).join('')||'<tr><td colspan="7" class="none">Sin resultados</td></tr>';
  document.querySelectorAll('th[data-k]').forEach(t=>{
    if(t.dataset.k===sk)t.setAttribute('aria-sort',sd<0?'descending':'ascending');else t.removeAttribute('aria-sort')});
}
document.querySelectorAll('th[data-k]').forEach(t=>t.onclick=()=>{
  const k=t.dataset.k;sd=(sk===k)?-sd:-1;sk=k;renderIns()});
/* ============ 5 INCIDENCIAS ============ */
const CN={insumos:'Insumos',higiene:'Higiene',tecnico:'Técnico',acceso:'Acceso',otros:'Otros'};
let cat='all', soloAbiertas=true;
function renderInc(){
  const q=nrm($('#qinc').value);
  const rows=D.incidencias.filter(i=>(cat==='all'||i.cat===cat)&&(!soloAbiertas||i.estado!=='resuelto')
    &&(!q||nrm(txtInc(i)).includes(q)));
  const nAb=D.incidencias.filter(i=>i.estado!=='resuelto').length;
  $('#ic').innerHTML=`<b>${rows.length}</b> de ${D.incidencias.length} · ${nAb} sin resolver`;
  $('#li').innerHTML=rows.length?'<div class="rows">'+rows.map(i=>{
      const c=carencia(i);return filaInc({...i,_c:c?c.txt:null,_hoy:conHuespedHoy(i)},false)}).join('')+'</div>'
    :'<div class="none">Sin incidencias</div>';
}
$('#iab').onclick=e=>{soloAbiertas=!soloAbiertas;
  e.target.setAttribute('aria-pressed',soloAbiertas?'true':'false');
  e.target.textContent=soloAbiertas?'Solo sin resolver':'Todas';renderInc()};
document.querySelectorAll('.cats button[data-c]').forEach(b=>b.onclick=()=>{
  document.querySelectorAll('.cats button[data-c]').forEach(x=>x.setAttribute('aria-pressed','false'));
  b.setAttribute('aria-pressed','true');cat=b.dataset.c;renderInc()});
/* ---- listeners ---- */
$('#hq').addEventListener('input',buscarGlobal);
['qp','fr'].forEach(i=>$('#'+i).addEventListener('input',renderProps));
['fa','far','qa'].forEach(i=>$('#'+i).addEventListener('input',renderAg));
['fcr','qc'].forEach(i=>$('#'+i).addEventListener('input',renderCal));
['fir','qi'].forEach(i=>$('#'+i).addEventListener('input',renderIns));
$('#qinc').addEventListener('input',renderInc);
$('#go').onclick=correr;
document.querySelectorAll('.q button').forEach(b=>b.onclick=()=>preset(+b.dataset.d,+b.dataset.n,+b.dataset.p,b.dataset.k==='1'));
pintarHome();renderProps();renderAg();renderCal();renderIns();renderInc();
$('#qd').value=D.ventana.desde;
const t2=base();t2.setDate(t2.getDate()+2);$('#qh').value=iso(t2);
correr();
