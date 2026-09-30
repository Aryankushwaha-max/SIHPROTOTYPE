const API='/api/v1';
let wells=[],events=[],map,markers=L.layerGroup(),eventMarkers=L.layerGroup(),circle,searchMarker,searchCenter=null,searchLabel='';
const $=s=>document.querySelector(s);
const title=s=>String(s??'').replaceAll('_',' ');
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
async function api(path,opts){const r=await fetch(API+path,opts);if(!r.ok)throw Error((await r.json()).detail||'Request failed');return r.json()}
function initMap(){map=L.map('map',{zoomControl:false}).setView([58.38,1.94],9);L.control.zoom({position:'bottomright'}).addTo(map);L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:18,attribution:'© OpenStreetMap'}).addTo(map);markers.addTo(map);eventMarkers.addTo(map);map.on('click',e=>setSearchLocation(e.latlng.lat,e.latlng.lng,'Map selection',true))}
function active(){return wells.find(w=>w.well_id===$('#activeWell').value)||wells[0]}
async function load(){
 try{
  [wells,events]=await Promise.all([api('/wells'),api('/events?limit=500').then(x=>x.items)]);
  if(!wells.length)return;
  $('#activeWell').innerHTML=wells.map(w=>`<option value="${esc(w.well_id)}">${esc(w.name)}${w.is_synthetic?' · synthetic':''}</option>`).join('');
  $('#activeWell').value=wells.find(w=>w.well_id==='15/9-F-9A')?.well_id||wells[0].well_id;
  const summary=await api('/analytics/summary');
  $('#eventCount').textContent=summary.event_count;
  $('#highCount').textContent=summary.high_severity_events;
  $('#activeCount').textContent=summary.synthetic_wells;
  const types=[...new Set(events.filter(e=>e.event_type!=='none').map(e=>e.event_type))].sort();
  $('#typeFilter').innerHTML='<option value="">All event types</option>'+types.map(t=>`<option value="${esc(t)}">${esc(title(t))}</option>`).join('');
  $('#riskForm').elements.md_m.value=619;
  focusWell(active());renderTelemetry();
  $('#activeWell').addEventListener('change',()=>focusWell(active()));$('#radius').addEventListener('change',render);
  $('#search').addEventListener('input',renderEvents);$('#typeFilter').addEventListener('change',renderEvents);$('#severityFilter').addEventListener('change',renderEvents);
  $('#clearFilters').addEventListener('click',()=>{$('#search').value='';$('#typeFilter').value='';$('#severityFilter').value='';renderEvents()});
  $('#riskForm').addEventListener('submit',assessForm);$('#ddrForm').addEventListener('submit',searchReports);
  $('#mapSearch').addEventListener('submit',searchWell);$('#coordinateSearch').addEventListener('submit',searchCoordinates);$('#useLocation').addEventListener('click',useDeviceLocation);
 }catch(e){$('#eventRows').innerHTML=`<tr><td colspan="5">Could not load dashboard: ${esc(e.message)}</td></tr>`}
}
function focusWell(w){if(!w)return;$('#activeWell').value=w.well_id;searchCenter={lat:w.latitude,lng:w.longitude};searchLabel=w.name;if(searchMarker){map.removeLayer(searchMarker);searchMarker=null}$('#locationMessage').textContent=`Showing wells near ${w.name}. Select a different well or map location to explore.`;render();map.flyTo([w.latitude,w.longitude],Number($('#radius').value)<=5?11:9,{duration:.55})}
function setSearchLocation(lat,lng,label,moveMap=false){searchCenter={lat:Number(lat),lng:Number(lng)};searchLabel=label;$('#coordinateQuery').value=`${searchCenter.lat.toFixed(5)}, ${searchCenter.lng.toFixed(5)}`;$('#locationMessage').textContent=`Showing wells within ${$('#radius').value} km of ${label}.`;if(searchMarker)map.removeLayer(searchMarker);searchMarker=L.circleMarker([lat,lng],{radius:7,color:'#344e46',weight:2,fillColor:'#fff',fillOpacity:1}).bindPopup(`<div class="popup-title">${esc(label)}</div><div class="popup-meta">${Number(lat).toFixed(5)}, ${Number(lng).toFixed(5)}</div>`).addTo(map);if(moveMap)map.flyTo([lat,lng],12,{duration:.55});render()}
function searchWell(ev){ev.preventDefault();const q=$('#locationQuery').value.trim().toLowerCase();if(!q)return;const w=wells.find(x=>x.well_id.toLowerCase()===q||x.name.toLowerCase()===q)||wells.find(x=>x.name.toLowerCase().includes(q)||x.well_id.toLowerCase().includes(q));if(!w){$('#locationMessage').textContent='No matching well found. Try a well ID or enter latitude and longitude.';return}focusWell(w)}
function searchCoordinates(ev){ev.preventDefault();const values=$('#coordinateQuery').value.trim().split(/[\s,;]+/).filter(Boolean).map(Number);const [lat,lng]=values;if(values.length!==2||!Number.isFinite(lat)||!Number.isFinite(lng)||Math.abs(lat)>90||Math.abs(lng)>180){$('#locationMessage').textContent='Enter coordinates as latitude, longitude (for example 58.38, 1.94).';return}setSearchLocation(lat,lng,'Selected coordinates',true)}
function useDeviceLocation(){if(!navigator.geolocation){$('#locationMessage').textContent='This browser does not support location sharing. Enter coordinates instead.';return}$('#locationMessage').textContent='Waiting for your device location…';navigator.geolocation.getCurrentPosition(pos=>setSearchLocation(pos.coords.latitude,pos.coords.longitude,'Your location',true),()=>{$('#locationMessage').textContent='Location was unavailable. Check your browser permission or enter coordinates instead.'},{enableHighAccuracy:true,timeout:10000,maximumAge:60000})}
function distance(a,b,c,d){const r=x=>x*Math.PI/180,y=r(c-a),z=r(d-b),h=Math.sin(y/2)**2+Math.cos(r(a))*Math.cos(r(c))*Math.sin(z/2)**2;return 6371.0088*2*Math.asin(Math.sqrt(h))}
function render(){
 const a=active();if(!a)return;const radius=Number($('#radius').value);if(!searchCenter){searchCenter={lat:a.latitude,lng:a.longitude};searchLabel=a.name}
 const nearby=wells.map(w=>({...w,distance_km:distance(searchCenter.lat,searchCenter.lng,w.latitude,w.longitude)})).filter(w=>w.distance_km<=radius).sort((x,y)=>x.distance_km-y.distance_km);
 $('#wellCount').textContent=nearby.length;
 $('#riskDepth').textContent=`${Number($('#riskForm').elements.md_m.value||619).toLocaleString()} m MD`;
 $('#nearbyLabel').textContent=`Within ${radius} km of ${searchLabel||'selected point'}`;
 markers.clearLayers();eventMarkers.clearLayers();
 nearby.forEach(w=>{
  const isActive=w.well_id===a.well_id;
  const color=isActive?'#168875':w.is_synthetic?'#d28a38':'#53839d';
  const marker=L.circleMarker([w.latitude,w.longitude],{radius:isActive?8:6,color,fillColor:color,fillOpacity:1,weight:2,bubblingMouseEvents:false})
   .bindPopup(`<div class="popup-title">${esc(w.name)}</div><div class="popup-meta">${esc(w.well_id)} · ${esc(w.field)}<br>${isActive?'Focus well':`${w.distance_km.toFixed(2)} km away`} · ${esc(w.source)}${w.is_synthetic?' · synthetic example':''}<br>Recorded total depth: ${Number(w.total_depth_m).toLocaleString()} m</div>`).addTo(markers);
  marker.on('click',()=>{if(!isActive)focusWell(w)});
 });
 if(circle)map.removeLayer(circle);
 circle=L.circle([searchCenter.lat,searchCenter.lng],{radius:radius*1000,color:'#78958b',weight:1,dashArray:'4 5',fillColor:'#9db9ac',fillOpacity:.045}).addTo(map);
 const inWell=events.filter(e=>e.event_type!=='none'&&nearby.some(w=>w.well_id===e.well_id));
 const hasCoords=new Map();for(const e of inWell)hasCoords.set(e.well_id,(hasCoords.get(e.well_id)||0)+1);
 for(const [wellId,count] of hasCoords){const w=wells.find(x=>x.well_id===wellId);if(!w)continue;
  L.marker([w.latitude,w.longitude],{icon:L.divIcon({className:'',html:`<div class="event-pin">${count}</div>`,iconSize:[18,18],iconAnchor:[9,9]}),bubblingMouseEvents:false})
   .bindPopup(`<div class="popup-title">${count} operational record${count===1?'':'s'}</div><div class="popup-meta">${esc(w.name)} · surface well location; event is downhole at recorded MD</div>`).addTo(eventMarkers);
 }
 renderNearbyList(nearby);
 map.setView([searchCenter.lat,searchCenter.lng],radius<=3?12:radius<=5?11:radius<=10?10:9);
 renderEvents();renderRisk(a,inWell);
}
function renderNearbyList(nearby){if(!nearby.length){$('#nearbyList').innerHTML='<p class="nearby-empty">No mapped wells fall inside this radius. Try widening the radius or choosing another location.</p>';return}$('#nearbyList').innerHTML=nearby.slice(0,7).map(w=>{const n=events.filter(e=>e.well_id===w.well_id&&e.event_type!=='none').length;return `<button class="nearby-item ${w.well_id===active().well_id?'selected':''}" type="button" data-well-id="${esc(w.well_id)}"><span class="nearby-name"><b>${esc(w.name)}</b><small>${esc(w.field)} · TD ${Number(w.total_depth_m).toLocaleString()} m${w.is_synthetic?' · synthetic':''}</small></span><span class="nearby-meta"><b>${w.distance_km.toFixed(1)} km</b><small>${n} event${n===1?'':'s'}</small></span></button>`}).join('');$('#nearbyList').querySelectorAll('[data-well-id]').forEach(button=>button.addEventListener('click',()=>focusWell(wells.find(w=>w.well_id===button.dataset.wellId))))}
function renderEvents(){
 const radius=Number($('#radius').value);const center=searchCenter||{lat:active().latitude,lng:active().longitude};
 const allowed=new Set(wells.filter(w=>distance(center.lat,center.lng,w.latitude,w.longitude)<=radius).map(w=>w.well_id));
 const q=$('#search').value.toLowerCase(),type=$('#typeFilter').value,sev=$('#severityFilter').value;
 const rows=events.filter(e=>e.event_type!=='none'&&allowed.has(e.well_id)&&(!type||e.event_type===type)&&(!sev||e.severity===sev)&&(!q||[e.summary,e.impact,e.well_id,e.formation,e.event_type,e.event_type_id].join(' ').toLowerCase().includes(q)));
 $('#eventRows').innerHTML=rows.map(e=>`<tr><td><span class="event-name">${esc(title(e.event_type))}</span><span class="event-id">${esc(e.event_id)} · ${esc(e.event_type_id)}</span></td><td><span class="event-name">${esc(wells.find(w=>w.well_id===e.well_id)?.name||e.well_id)}</span><span class="event-id">${Number(e.md_m).toLocaleString()} m MD · ${esc(e.report_date)}</span></td><td>${esc(e.formation)}</td><td><span class="severity ${esc(e.severity)}">${esc(e.severity)}</span></td><td><div class="summary">${esc(e.summary)}</div><div class="mitigation">${esc(e.impact)} · ${Math.round((e.confidence||0)*100)}% extraction confidence</div></td></tr>`).join('');
 $('#emptyState').hidden=rows.length>0;
}
function renderRisk(a,visibleEvents){
 const depth=Number($('#riskForm').elements.md_m.value||619);
 const candidates=visibleEvents.filter(e=>Math.abs(e.md_m-depth)<=350).sort((x,y)=>Math.abs(x.md_m-depth)-Math.abs(y.md_m-depth));
 if(!candidates.length){$('#riskList').innerHTML='<div class="normal-card">✓<b>No nearby event in selected radius</b><span>No structured record close to this measured depth.</span></div>';return}
 $('#riskList').innerHTML=candidates.slice(0,4).map(e=>`<article class="risk-card ${e.severity}"><h3>${esc(title(e.event_type))} · ${esc(e.severity)} severity</h3><p>${esc(e.formation)} at ${Number(e.md_m).toLocaleString()} m MD — ${esc(e.summary)}</p><a href="#eventRows" data-event="${esc(e.event_id)}">Offset ${esc(e.event_id)} ↗</a></article>`).join('');
 $('#riskList').querySelectorAll('[data-event]').forEach(link=>link.addEventListener('click',()=>{$('#search').value=link.dataset.event;renderEvents()}));
}
async function assessForm(ev){
 ev.preventDefault();const f=new FormData(ev.currentTarget),body={well_id:active().well_id};
 for(const k of ['md_m','flow_delta_pct','mud_loss_rate_m3h','torque_knm'])body[k]=Number(f.get(k));body.radius_km=Number($('#radius').value);
 try{const result=await api('/risks/assess',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
  const box=$('#assessmentResult');box.className='assessment-result'+(result.signals.length?' alert':'');
  box.innerHTML=`<b>${esc(result.overall_level.toUpperCase())}</b> · ${result.signals.length?result.signals.map(s=>`${esc(title(s.risk_type))}: ${esc(s.reason)}`).join('<br>'):'No configured threshold triggered.'}<br><small>${esc(result.disclaimer)}</small>`;
  $('#riskDepth').textContent=`${body.md_m.toLocaleString()} m MD`;renderRisk(active(),events.filter(e=>e.well_id===active().well_id));
 }catch(e){$('#assessmentResult').textContent=e.message}
}
function renderTelemetry(){
 api('/telemetry?limit=800').then(data=>{
  const points=data.points.filter(p=>p.depth_m!==null),width=1000,height=235,pad=30;
  const x=d=>pad+(d-points[0].depth_m)/(points.at(-1).depth_m-points[0].depth_m)*(width-2*pad);
  const paths=[];
  for(const [key,color] of [['torque_knm','#168875'],['rotary_rpm','#d28a38']]){
   const values=points.map(p=>p[key]).filter(v=>v!==null);const max=Math.max(...values,1);
   const line=points.map((p,i)=>p[key]===null?null:`${i?'L':'M'}${x(p.depth_m).toFixed(1)},${(height-pad-(p[key]/max)*(height-2*pad)).toFixed(1)}`).filter(Boolean).join(' ');
   paths.push(`<path d="${line}" fill="none" stroke="${color}" stroke-width="2" stroke-linejoin="round"/>`);
  }
  const incidentX=x(data.incident_reference.depth_m);
  $('#telemetryChart').innerHTML=`<svg viewBox="0 0 ${width} ${height}" role="img" aria-label="Historical torque and rotary speed versus measured depth"><line x1="${pad}" y1="${height-pad}" x2="${width-pad}" y2="${height-pad}" stroke="#dfe6e9"/><line x1="${incidentX}" y1="${pad}" x2="${incidentX}" y2="${height-pad}" stroke="#bd5650" stroke-dasharray="5 5"/>${paths.join('')}<text x="${incidentX+5}" y="18" fill="#ad5951" font-size="12">619 m · archived stuck-pipe reference</text><text x="${pad}" y="${height-7}" fill="#82919a" font-size="11">${points[0].depth_m.toFixed(0)} m MD</text><text x="${width-pad-60}" y="${height-7}" fill="#82919a" font-size="11">${points.at(-1).depth_m.toFixed(0)} m MD</text></svg>`;
  $('#telemetryNote').textContent=`${data.source_records.toLocaleString()} archived records · ${points.length.toLocaleString()} plotted samples · two series independently scaled for display. Historical public data, not a live stream.`;
 }).catch(e=>{$('#telemetryNote').textContent=`Telemetry trace unavailable: ${e.message}`});
}
async function searchReports(ev){
 ev.preventDefault();const q=$('#ddrQuery').value.trim();if(q.length<2)return;
 $('#ddrResults').innerHTML='<div class="ddr-empty">Searching archived reports…</div>';
 try{const result=await api(`/ddrs?q=${encodeURIComponent(q)}&limit=20`);
  $('#ddrResults').innerHTML=result.items.length?result.items.map(r=>`<article class="ddr-record"><div class="ddr-record-head"><b>${esc(r.hazard||'unclassified')} · ${esc(r.severity||'')}</b><span>${esc(r.report_date||'')} · ${Number(r.md_m||0).toLocaleString()} m MD</span></div><p>${esc(r.text)}</p><small>${esc(r.attribution_status)}</small></article>`).join(''):`<div class="ddr-empty">No report excerpts matched “${esc(q)}”.</div>`;
 }catch(e){$('#ddrResults').innerHTML=`<div class="ddr-empty">Search failed: ${esc(e.message)}</div>`}
}
document.addEventListener('DOMContentLoaded',()=>{initMap();load()});
