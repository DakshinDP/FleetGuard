const $ = (id) => document.getElementById(id);
const tokenKey = 'fleetguard_token';
let token = localStorage.getItem(tokenKey);
const escapeHtml = (s) => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
async function api(path, options={}) {
  const res = await fetch(`/api${path}`, {...options, headers:{'Content-Type':'application/json','Authorization':`Bearer ${token}`,...options.headers}});
  if (res.status === 401) { logout(); throw new Error('Session expired. Please sign in again.'); }
  const data = await res.json().catch(()=>({detail:'Unexpected server response'}));
  if (!res.ok) throw new Error(data.detail || 'Request failed');
  return data;
}
function show() { $('login').hidden=!!token; $('app').hidden=!token; $('session').hidden=!token; if(token){$('user').textContent='Fleet manager';refreshAll();} }
function logout(){token=null;localStorage.removeItem(tokenKey);show();}
function toast(message){$('toast').textContent=message;$('toast').style.display='block';setTimeout(()=>$('toast').style.display='none',2600);}
async function refreshAll(){try{const [s,a,v]=await Promise.all([api('/v1/fleet/summary'),api('/v1/alerts?limit=12'),api('/v1/vehicles?limit=12&q='+encodeURIComponent($('search').value))]);$('vehicles').textContent=s.vehicles.toLocaleString();$('open').textContent=s.open_alerts.toLocaleString();$('critical').textContent=s.critical_alerts.toLocaleString();$('events').textContent=s.events_5m.toLocaleString();$('alerts').innerHTML=a.items.map(x=>`<tr><td>${escapeHtml(x.vehicle_id)}</td><td>${escapeHtml(x.title)}</td><td><span class="badge ${escapeHtml(x.severity)}">${escapeHtml(x.severity)}</span></td><td>${x.risk_score}</td><td>${new Date(x.event_ts).toLocaleTimeString()}</td><td>${x.acknowledged_at?'Done':`<button class="ack" data-ack="${escapeHtml(x.alert_id)}">Acknowledge</button>`}</td></tr>`).join('');$('empty').hidden=a.items.length>0;$('vehicle-rows').innerHTML=v.items.map(x=>`<tr><td>${escapeHtml(x.vehicle_id)}</td><td>${escapeHtml(x.make)}</td><td>${escapeHtml(x.model)}</td><td>${x.model_year}</td><td>${escapeHtml(x.powertrain)}</td><td>${escapeHtml(x.status)}</td></tr>`).join('');$('vehicle-more').textContent=v.next_after?'Showing first 12 vehicles. Refine the search to narrow results.':'';}catch(e){toast(e.message)}}
$('login-form').addEventListener('submit',async e=>{e.preventDefault();$('login-error').textContent='';const form=new FormData(e.currentTarget);try{const res=await fetch('/api/v1/auth/token',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email:form.get('email'),password:form.get('password')})});const data=await res.json();if(!res.ok)throw new Error(data.detail||'Sign in failed');token=data.access_token;localStorage.setItem(tokenKey,token);show();}catch(err){$('login-error').textContent=err.message;}});
$('logout').addEventListener('click',logout);$('refresh').addEventListener('click',refreshAll);$('search').addEventListener('input',()=>{clearTimeout(window.searchTimer);window.searchTimer=setTimeout(refreshAll,250)});
$('alerts').addEventListener('click',async e=>{const id=e.target.dataset.ack;if(!id)return;try{await api(`/v1/alerts/${id}/ack`,{method:'POST',body:JSON.stringify({note:'Reviewed in dashboard'})});toast('Alert acknowledged');refreshAll()}catch(err){toast(err.message)}});
show();setInterval(()=>{if(token)refreshAll()},7000);
