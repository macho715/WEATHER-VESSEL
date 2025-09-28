diff --git a/logistics_control_tower_v2.html b/logistics_control_tower_v2.html
index bb2612ea5d46286a36cd032a1e7c8ea8afaa3aaf..2178a725dd980b2d7610cd6649aba355fac580c4 100644
--- a/logistics_control_tower_v2.html
+++ b/logistics_control_tower_v2.html
@@ -1,81 +1,91 @@
 <!DOCTYPE html>
 <html lang="ko">
 <head>
   <meta charset="UTF-8" />
   <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
   <title>Logistics Control Tower v2.5</title>
   <script src="https://cdn.tailwindcss.com"></script>
   <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" crossorigin=""/>
   <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js" crossorigin=""></script>
   <style>
-    body{background:#0f172a;color:#e2e8f0;font-family:'Segoe UI',sans-serif}
+    body{background:radial-gradient(circle at top,#1e293b 0%,#0f172a 55%,#020617 100%);color:#e2e8f0;font-family:'Segoe UI',sans-serif}
     .leaflet-container{background:#1f2937;border-radius:.75rem}
     .leaflet-tooltip{background:rgba(15,23,42,.95);color:#fff;border:1px solid #475569;box-shadow:none;font-weight:600;padding:4px 8px}
     .scrollbar-hide::-webkit-scrollbar{display:none}.scrollbar-hide{-ms-overflow-style:none;scrollbar-width:none}
     .modal{transition:opacity .25s ease;z-index:10000}
     body.modal-open{overflow:hidden}
     #map{position:relative;z-index:0}
     .leaflet-tooltip,.leaflet-popup{z-index:500!important}
     .row-current{background:rgba(59,130,246,.15)}
     .kbd{border:1px solid #475569;border-bottom-width:2px;border-radius:.375rem;padding:.15rem .35rem;font-family:ui-monospace,SFMono-Regular,Menlo,monospace}
-    .tag{font-size:.75rem;padding:.1rem .4rem;border:1px solid #475569;border-radius:.5rem}
+    .tag{font-size:.75rem;padding:.1rem .4rem;border:1px solid rgba(148,163,184,.6);border-radius:.5rem;background:rgba(148,163,184,.12)}
     .chip{display:inline-flex;align-items:center;gap:.25rem;padding:.25rem .5rem;border-radius:.5rem;background:rgba(79,70,229,.2);color:#c7d2fe;font-size:.75rem}
     .sr-only{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0}
     .btn { min-height: 44px; min-width: 44px; } /* 터치 타겟 44px 기준 */
+    .panel-scroll{max-height:clamp(260px,45vh,520px);overflow-y:auto;scrollbar-color:#475569 transparent}
+    .panel-scroll::-webkit-scrollbar{width:6px}
+    .panel-scroll::-webkit-scrollbar-thumb{background:rgba(148,163,184,.45);border-radius:9999px}
+    .pill{display:inline-flex;align-items:center;gap:.25rem;padding:.2rem .6rem;border-radius:9999px;font-weight:600;font-size:.75rem;border:1px solid rgba(94,234,212,.3);background:rgba(45,212,191,.12);color:#a7f3d0;text-transform:uppercase;letter-spacing:.02em}
+    .pill-success{background:rgba(34,197,94,.18);border-color:rgba(34,197,94,.4);color:#bbf7d0}
+    .pill-warn{background:rgba(234,179,8,.22);border-color:rgba(234,179,8,.45);color:#fef3c7}
+    .pill-danger{background:rgba(248,113,113,.2);border-color:rgba(248,113,113,.45);color:#fecaca}
+    #assistant-dropzone{transition:background .2s ease,border-color .2s ease}
+    #assistant-dropzone.drop-active{border-color:rgba(14,165,233,.75);background:rgba(14,165,233,.08);box-shadow:0 0 0 1px rgba(14,165,233,.2)}
+    #assistant-attachments img{box-shadow:0 4px 12px rgba(15,23,42,.65)}
 
     @media (prefers-contrast: more) {
         :root {
             --accent: #00b4ff;
             --text: #ffffff;
             --muted: #e2e8f0;
         }
         .panel, .status-card, .control-card { border-color: rgba(255,255,255,0.6); }
-        .pill { background: rgba(0,180,255,0.25); }
+        .pill, .pill-success, .pill-warn, .pill-danger { border-color: rgba(255,255,255,0.7); }
     }
   </style>
 </head>
 <body class="p-4">
   <!-- Skip link for keyboard users -->
   <a href="#main" class="sr-only" style="position:absolute;left:-9999px;top:auto;width:1px;height:1px;overflow:hidden;"
      onfocus="this.style.position='static';this.style.width='auto';this.style.height='auto';this.style.padding='0.5rem 0.75rem';this.style.background='#0ea5e9';this.style.color='#000';this.style.borderRadius='8px';">
      Skip to main content
   </a>
   <main id="main" class="grid grid-cols-1 lg:grid-cols-5 gap-4 h-[95vh]" role="main" aria-live="polite">
     <div id="map" class="lg:col-span-3 rounded-xl shadow-xl border border-slate-700 h-full min-h-[400px]" 
          role="img" aria-label="Vessel tracking map showing route from MW4 to AGI" tabindex="0"></div>
 
     <aside class="lg:col-span-2 flex flex-col gap-4 h-full" role="complementary" aria-label="Vessel control and schedule information">
-      <div id="info-panel" class="bg-slate-900 p-4 rounded-xl shadow-lg border border-slate-700">
+      <div id="info-panel" class="bg-slate-900/90 p-4 rounded-xl shadow-2xl border border-slate-700 panel-scroll backdrop-blur-sm space-y-4">
         <div class="flex items-center justify-between">
           <h2 class="text-xl font-bold border-b border-slate-600 pb-2 mb-3">Vessel Control</h2>
           <div class="flex items-center gap-2">
             <span class="tag">Local: Asia/Dubai</span>
-            <div class="pill" id="marineBadge" title="Marine snapshot">Hs: -- m · Wind: -- kt</div>
+            <div class="pill pill-warn" id="marineBadge" title="Marine snapshot">Hs: -- m · Wind: -- kt</div>
           </div>
         </div>
-        <div id="vessel-info"><p class="text-slate-400">Loading vessel data...</p></div>
+        <div id="vessel-info" class="space-y-4"><p class="text-slate-400">Loading vessel data...</p></div>
 
         <div class="grid grid-cols-2 gap-2 mt-4">
           <button id="briefing-btn" class="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-2 px-3 rounded-lg transition-colors flex items-center justify-center gap-2 text-sm"
                   aria-describedby="briefing-desc">✨ Daily Briefing</button>
           <button id="assistant-btn" class="w-full bg-purple-600 hover:bg-purple-700 text-white font-bold py-2 px-3 rounded-lg transition-colors flex items-center justify-center gap-2 text-sm"
                   aria-describedby="assistant-desc">🤖 Ask AI Assistant</button>
         </div>
         <div class="sr-only" id="briefing-desc">Generate AI-powered daily logistics briefing</div>
         <div class="sr-only" id="assistant-desc">Open AI assistant chat for logistics questions</div>
 
         <div class="mt-4 grid grid-cols-2 gap-2">
           <label class="w-full">
             <input type="file" id="file-schedule" class="hidden" accept=".csv,.json"/>
             <span id="label-schedule" class="w-full inline-flex items-center justify-center bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-3 rounded-lg cursor-pointer">Upload Schedule (CSV/JSON)</span>
           </label>
           <label class="w-full">
             <input type="file" id="file-weather" class="hidden" accept=".csv"/>
             <span id="label-weather" class="w-full inline-flex items-center justify-center bg-emerald-600 hover:bg-emerald-700 text-white font-bold py-2 px-3 rounded-lg cursor-pointer">Upload Weather (CSV)</span>
           </label>
         </div>
         <p class="mt-3 text-xs text-slate-400">Tips: Press <span class="kbd">Esc</span> to close modals. 파일 포맷은 하단 가이드를 참고. API는 <span class="chip" id="api-status">API: Offline</span></p>
       </div>
 
       <div class="bg-slate-900 p-4 rounded-xl shadow-lg border border-slate-700 flex-grow flex flex-col h-1/2">
         <div class="flex items-center justify-between border-b border-slate-600 pb-2 mb-3">
@@ -128,97 +138,100 @@
        role="dialog" aria-modal="true" aria-labelledby="modal-title" aria-describedby="modal-content" aria-hidden="true">
     <div class="bg-slate-900 rounded-xl shadow-2xl p-6 w-full max-w-lg border border-slate-700" role="document">
       <h2 id="modal-title" class="text-2xl font-bold text-indigo-400 mb-4">✨ AI-Generated Output</h2>
       <div id="modal-content" class="text-slate-300 bg-slate-950 p-4 rounded-md min-h-[150px] whitespace-pre-line overflow-y-auto max-h-[60vh]"></div>
       <button id="close-modal-btn" class="mt-6 w-full bg-slate-700 hover:bg-slate-600 text-white font-bold py-2 px-4 rounded-lg transition-colors">Close</button>
     </div>
   </div>
 
   <div id="assistant-modal" class="modal fixed inset-0 bg-black bg-opacity-70 flex items-center justify-center p-4 opacity-0 pointer-events-none"
        role="dialog" aria-modal="true" aria-labelledby="assistant-title" aria-describedby="assistant-conversation" aria-hidden="true">
     <div class="bg-slate-900 rounded-xl shadow-2xl p-6 w-full max-w-2xl border border-slate-700 flex flex-col h-[80vh]" role="document">
       <div class="flex items-center justify-between mb-4">
         <h2 id="assistant-title" class="text-2xl font-bold text-purple-400">🤖 AI Logistics Assistant</h2>
         <div class="flex items-center gap-2">
           <label class="text-xs text-slate-300">Model
             <select id="assistant-model" class="ml-2 bg-slate-800 border border-slate-600 text-slate-100 text-xs rounded px-2 py-1">
               <option value="gpt-4.1-mini">gpt-4.1-mini</option>
               <option value="gpt-4o-mini">gpt-4o-mini</option>
             </select>
           </label>
         </div>
       </div>
       <div id="assistant-conversation" class="flex-grow bg-slate-950 p-4 rounded-md overflow-y-auto scrollbar-hide space-y-2 text-sm">
         <div class="text-slate-400">무엇을 도와드릴까요? (예: “다음 3일 스케줄 요약”)<br/>첨부 버튼으로 캡처/문서를 추가하면 자동 분석됩니다.</div>
       </div>
-      <div class="mt-3 bg-slate-800/60 border border-slate-600 rounded-lg p-3">
+      <div id="assistant-dropzone" class="mt-3 bg-slate-800/60 border border-dashed border-slate-600 rounded-lg p-3">
         <div class="flex items-center justify-between">
           <div class="text-xs text-slate-300 font-semibold">Attachments</div>
           <button id="assistant-attach-btn" class="text-xs bg-slate-700 hover:bg-slate-600 text-white px-2 py-1 rounded">+ Add</button>
         </div>
+        <p class="mt-2 text-[11px] text-slate-400">+ 버튼을 누르거나 파일을 끌어다 놓고, 스크린 캡처는 붙여넣기(Ctrl/⌘+V)로 추가하세요.</p>
         <input type="file" id="assistant-file" class="hidden" accept="image/*,.pdf,.txt,.csv" multiple />
-        <div id="assistant-attachments" class="mt-2 text-xs text-slate-400 space-y-1"></div>
+        <div id="assistant-attachments" class="mt-3 text-xs text-slate-300 space-y-2 min-h-[3rem]" aria-live="polite"></div>
       </div>
       <form id="assistant-form" class="mt-3 flex gap-2" role="form" aria-label="AI Assistant Chat">
         <input type="text" id="assistant-input" class="flex-grow bg-slate-800 text-white rounded-lg p-2 border border-slate-600 focus:outline-none focus:ring-2 focus:ring-purple-500" 
                placeholder="Ask a question..." aria-label="Type your question here" aria-describedby="assistant-input-desc">
         <button type="submit" class="bg-purple-600 hover:bg-purple-700 text-white font-bold py-2 px-4 rounded-lg transition-colors"
                 aria-label="Send message">Send</button>
       </form>
       <div class="sr-only" id="assistant-input-desc">Type your logistics question and press Enter or click Send</div>
       <div class="flex gap-2 mt-2 text-xs text-slate-400">
         <button id="assistant-reset" type="button" class="px-3 py-1 rounded bg-slate-700 hover:bg-slate-600 text-white">Clear Chat</button>
         <span id="assistant-usage" class="italic"></span>
       </div>
       <button id="close-assistant-btn" class="mt-3 w-full bg-slate-700 hover:bg-slate-600 text-white font-bold py-2 px-4 rounded-lg transition-colors">Close</button>
     </div>
   </div>
 
   <script>
     // requestIdleCallback 폴리필 (간단)
     window.requestIdleCallback ||= (cb)=>setTimeout(()=>cb({didTimeout:false,timeRemaining:()=>0}), 1);
     window.cancelIdleCallback ||= (id)=>clearTimeout(id);
 
   document.addEventListener('DOMContentLoaded', () => {
     const API_BASE = window.APP_CONFIG?.apiBase ?? 'http://localhost:8000';
     const tz = 'Asia/Dubai';
     
     // Scenario presets and port coordinates
     const scenarioPresets = {
       base:        { delayOnRisk: 4.0,  hs_caution: 1.50, hs_nogo: 2.50, wind_caution: 18, wind_nogo: 28 },
       weather:     { delayOnRisk: 6.0,  hs_caution: 1.20, hs_nogo: 2.00, wind_caution: 16, wind_nogo: 24 },
       congestion:  { delayOnRisk: 5.0,  hs_caution: 1.60, hs_nogo: 2.60, wind_caution: 20, wind_nogo: 30 },
       inspection:  { delayOnRisk: 3.5, hs_caution: 1.80, hs_nogo: 2.80, wind_caution: 22, wind_nogo: 32 }
     };
     const RULE = scenarioPresets.base;
     
     const portCoords = {
       'Shanghai':   { lat: 31.2304, lon: 121.4737 },
       'Singapore':  { lat: 1.3521,  lon: 103.8198 },
       'Colombo':    { lat: 6.9271,  lon: 79.8612  },
       'Jebel Ali':  { lat: 25.006,  lon: 55.065   }
     };
+    const MARINE_CACHE_TTL_MS = 5 * 60 * 1000;
+    const marineSnapshotCache = new Map();
     const fmtIso = (d)=> new Date(d).toISOString();
     const toLocal = (d)=> new Date(d).toLocaleString('en-GB',{ timeZone: tz, dateStyle:'short', timeStyle:'medium' });
     const pad2 = (n)=> String(n).padStart(2,'0');
     const clamp = (v,min,max)=> Math.max(min, Math.min(max,v));
     const parseNum = (s)=> Number(String(s||'').trim());
     const parseISO = (s)=> {
       if(!s) return null;
       const t = String(s).trim().replace(' ', 'T');
       return isNaN(Date.parse(t)) ? null : new Date(t);
     };
     const parseCSV = (text)=>{
       const lines = text.trim().split(/\r?\n/);
       const header = lines.shift().split(',').map(h=>h.trim());
       return lines.map(line=>{
         const cells = line.split(',').map(c=>c.trim());
         const obj={};
         header.forEach((h,i)=> obj[h]=cells[i]);
         return obj;
       });
     };
 
     async function checkApiHealth(){
       const badge = document.getElementById('api-status');
       try{
         const res = await fetch(`${API_BASE}/health`);
@@ -286,99 +299,138 @@
     }
     const segments=[]; let totalMeters=0;
     for(let i=0;i<vesselData.route.length-1;i++){
       const a=vesselData.route[i], b=vesselData.route[i+1];
       const m=haversine(a,b);
       segments.push({a,b,m,accStart:totalMeters,accEnd:totalMeters+m});
       totalMeters+=m;
     }
     function interpolateOnRoute(progress){
       const target=clamp(progress,0,1)*totalMeters;
       const seg=segments.find(s=>target>=s.accStart && target<=s.accEnd) || segments[segments.length-1];
       const t=(target-seg.accStart)/(seg.m||1);
       const lat=seg.a[0]+(seg.b[0]-seg.a[0])*t;
       const lon=seg.a[1]+(seg.b[1]-seg.a[1])*t;
       return [Number(lat.toFixed(5)), Number(lon.toFixed(5))];
     }
 
     const infoPanel = document.getElementById('vessel-info');
     const timeDisplay = document.getElementById('sim-time');
     const scheduleContainer = document.getElementById('schedule-container');
     const alertContainer = document.getElementById('alert-container');
     const assistantConversation = document.getElementById('assistant-conversation');
     const assistantUsage = document.getElementById('assistant-usage');
     const assistantFileInput = document.getElementById('assistant-file');
     const assistantAttachments = document.getElementById('assistant-attachments');
+    const assistantDropzone = document.getElementById('assistant-dropzone');
     const assistantModelSelect = document.getElementById('assistant-model');
     let assistantHistory = [];
     let pendingAttachments = [];
 
     function updateInfoPanel(){
       const cur=vesselData.currentVoyageId||'N/A';
+      const activeLeg = voyageSchedule.find(v=>v.id===vesselData.currentVoyageId);
+      const progressRatio = clamp(vesselData.progress ?? 0,0,1);
+      const progressPct = progressRatio * 100;
+      const etdDisplay = activeLeg?.etd ? toLocal(activeLeg.etd) : 'N/A';
+      const etaDisplay = activeLeg?.eta ? toLocal(activeLeg.eta) : 'N/A';
       infoPanel.innerHTML =
-        `<h3 class="text-2xl font-bold text-cyan-400">${vesselData.name}</h3>
-         <p class="text-sm text-slate-400">IMO: ${vesselData.imo} / MMSI: ${vesselData.mmsi}</p>
-         <div class="mt-4 space-y-2">
-           <div><strong>Current Voyage:</strong> <span class="font-mono text-lg">${cur}</span></div>
-           <div><strong>Status:</strong> <span class="font-mono text-lg text-yellow-300">${vesselData.status}</span></div>
+        `<div class="flex items-start justify-between gap-3">
+           <div>
+             <h3 class="text-2xl font-bold text-cyan-400">${vesselData.name}</h3>
+             <p class="text-sm text-slate-400">IMO: ${vesselData.imo} / MMSI: ${vesselData.mmsi}</p>
+           </div>
+           <span class="px-2 py-1 rounded-md text-xs bg-slate-800/80 border border-slate-600">${tz}</span>
+         </div>
+         <div class="grid grid-cols-2 gap-3 text-sm">
+           <div class="bg-slate-800/60 border border-slate-700 rounded-lg p-3">
+             <p class="text-slate-400 text-xs uppercase tracking-wider">Current Voyage</p>
+             <p class="mt-1 font-mono text-lg text-emerald-300">${cur}</p>
+           </div>
+           <div class="bg-slate-800/60 border border-slate-700 rounded-lg p-3">
+             <p class="text-slate-400 text-xs uppercase tracking-wider">Status</p>
+             <p class="mt-1 font-semibold text-sky-300">${vesselData.status}</p>
+           </div>
+         </div>
+         <div class="bg-slate-800/60 border border-slate-700 rounded-lg p-3">
+           <div class="flex items-center justify-between text-xs text-slate-400">
+             <span>Leg Progress</span>
+             <span class="font-mono text-slate-200">${progressPct.toFixed(2)}%</span>
+          </div>
+          <div class="w-full h-2 bg-slate-900/80 rounded-full mt-2">
+             <div class="h-2 rounded-full bg-gradient-to-r from-cyan-400 via-sky-500 to-emerald-400" style="width:${Math.min(100,Math.max(0,progressPct)).toFixed(2)}%"></div>
+           </div>
+           <div class="mt-3 grid grid-cols-2 gap-2 text-xs text-slate-400">
+             <div>
+               <span class="block uppercase tracking-wide">ETD</span>
+               <span class="font-mono text-slate-200">${etdDisplay}</span>
+             </div>
+             <div>
+               <span class="block uppercase tracking-wide">ETA</span>
+               <span class="font-mono text-slate-200">${etaDisplay}</span>
+             </div>
+           </div>
          </div>`;
     }
 
     async function renderSchedule(){
       const scheduleBody = document.getElementById('schedule-body');
       if (!scheduleBody) return;
       
       document.getElementById('schedule-container').setAttribute('aria-busy','true');
       scheduleBody.innerHTML = '';
       
+      const marineSnap = await updateMarineForLeg('Jebel Ali');
+      const baseIoi = Number.isFinite(marineSnap?.ioi) ? Number(marineSnap.ioi) : 50;
+
       for (let index = 0; index < voyageSchedule.length; index += 1) {
         const v = voyageSchedule[index];
         let c="text-slate-300", pill="";
         if(v.status==="In Transit") { c="text-blue-300"; pill='<span class="tag">Sailing</span>'; }
         else if(v.status==="Delayed") { c="text-rose-300"; pill='<span class="tag">Delayed</span>'; }
         else if(v.status==="Completed") { c="text-emerald-300"; pill='<span class="tag">Arrived</span>'; }
         const hi=v.id===vesselData.currentVoyageId ? "row-current" : "";
-        
+
         // Marine data for this port (simplified for current structure)
-        const snap = await updateMarineForLeg('Jebel Ali'); // Default port for now
-        const ioi = snap?.ioi ?? 50;
-        const decision = ioi >= 75 ? { tag: 'Go', tone: 'success' } : 
-                        ioi >= 55 ? { tag: 'Caution', tone: 'warn' } : 
+        const ioi = baseIoi;
+        const decision = ioi >= 75 ? { tag: 'Go', tone: 'success' } :
+                        ioi >= 55 ? { tag: 'Caution', tone: 'warn' } :
                         { tag: 'No-Go', tone: 'danger' };
-        
+        const formattedIoi = Number.isFinite(ioi) ? Number(ioi).toFixed(2) : '50.00';
+
         const row = document.createElement('tr');
         row.id = `voyage-${v.id}`;
         row.className = `border-t border-slate-700 ${hi}`;
         row.setAttribute('role', 'row');
         row.innerHTML = `
           <td class="p-2 font-bold" role="gridcell" aria-describedby="th-voyage">${v.id}</td>
           <td class="p-2" role="gridcell" aria-describedby="th-cargo">${v.cargo}</td>
           <td class="p-2" role="gridcell" aria-describedby="th-etd">${toLocal(v.etd)}</td>
           <td class="p-2" role="gridcell" aria-describedby="th-eta">${toLocal(v.eta)}</td>
           <td class="p-2 ${c} font-semibold" role="gridcell" aria-describedby="th-status">${v.status} ${pill}</td>
-          <td class="p-2" role="gridcell" aria-describedby="th-ioi">${ioi}</td>
-          <td class="p-2" role="gridcell" aria-describedby="th-decision"><span class="pill ${decision.tone === 'danger' ? 'danger' : ''}">${decision.tag}</span></td>
+          <td class="p-2" role="gridcell" aria-describedby="th-ioi">${formattedIoi}</td>
+          <td class="p-2" role="gridcell" aria-describedby="th-decision"><span class="pill pill-${decision.tone}">${decision.tag}</span></td>
         `;
         scheduleBody.appendChild(row);
       }
       
       document.getElementById('schedule-container').setAttribute('aria-busy','false');
 
       if(vesselData.currentVoyageId){
         const row=document.getElementById(`voyage-${vesselData.currentVoyageId}`);
         if(row) row.scrollIntoView({block:'center',behavior:'smooth'});
       }
     }
 
     function setInfo(msgHtml, tone='info'){
       const color = tone==='warn' ? 'bg-yellow-900 border-yellow-500 text-yellow-100'
                    : tone==='danger' ? 'bg-rose-900 border-rose-500 text-rose-100'
                    : 'bg-slate-950 border-slate-600 text-slate-200';
       alertContainer.innerHTML = `<div class="${color} px-4 py-3 rounded border">${msgHtml}</div>`;
     }
 
     const LIM = {
       waveWarnM: 1.75, waveNoGoM: 2.25,
       windWarnKt: 24, windNoGoKt: 30,
       visNoGoKm: 1.0
     };
 
@@ -557,120 +609,190 @@
     });
 
     const briefingModal=document.getElementById('briefing-modal');
     const assistantModal=document.getElementById('assistant-modal');
     const modalTitle=document.getElementById('modal-title');
     const modalContent=document.getElementById('modal-content');
 
     function openModal(el){ 
       el.classList.remove('opacity-0','pointer-events-none'); 
       el.setAttribute('aria-hidden', 'false');
       document.body.classList.add('modal-open'); 
       // Focus management
       const focusableElements = el.querySelectorAll('button, input, select, textarea, [tabindex]:not([tabindex="-1"])');
       if(focusableElements.length > 0) {
         focusableElements[0].focus();
       }
     }
     function closeModal(el){ 
       el.classList.add('opacity-0','pointer-events-none'); 
       el.setAttribute('aria-hidden', 'true');
       document.body.classList.remove('modal-open'); 
     }
     [briefingModal,assistantModal].forEach(m=> m.addEventListener('click', e=>{ if(e.target===m) closeModal(m); }));
     document.addEventListener('keydown', e=>{ if(e.key==='Escape'){ [briefingModal,assistantModal].forEach(closeModal); } });
 
+    function guessExtension(type){
+      if(!type) return '';
+      if(type.includes('png')) return '.png';
+      if(type.includes('jpeg') || type.includes('jpg')) return '.jpg';
+      if(type.includes('gif')) return '.gif';
+      if(type.includes('webp')) return '.webp';
+      if(type.includes('pdf')) return '.pdf';
+      if(type.includes('csv')) return '.csv';
+      if(type.includes('plain')) return '.txt';
+      return '';
+    }
+
+    function addAttachmentsFromFileList(fileList){
+      const files = Array.from(fileList || []);
+      if(files.length===0) return;
+      const stamped = files.map((file,idx)=>{
+        if(file.name) return file;
+        const ext = guessExtension(file.type || '');
+        const timestamp = new Date().toISOString().replace(/[.:]/g,'-');
+        return new File([file], `capture-${timestamp}-${idx+1}${ext}`, { type: file.type || 'application/octet-stream' });
+      });
+      pendingAttachments = pendingAttachments.concat(stamped);
+      renderAttachmentList();
+    }
+
     function renderAttachmentList(){
       if(pendingAttachments.length===0){
-        assistantAttachments.innerHTML = '<div class="text-slate-500">No attachments selected.</div>';
+        assistantAttachments.innerHTML = '<div class="text-slate-500 text-[11px]">첨부된 파일이 없습니다. 스크린 캡처 붙여넣기를 지원합니다.</div>';
         return;
       }
       assistantAttachments.innerHTML = pendingAttachments.map((file,idx)=>{
-        return `<div class="flex justify-between items-center bg-slate-900/80 px-2 py-1 rounded">
-                  <span class="truncate max-w-[14rem]">${file.name}</span>
-                  <button data-index="${idx}" class="text-rose-300 hover:text-rose-400 remove-attachment">Remove</button>
+        const isImage = (file.type || '').startsWith('image/');
+        const preview = isImage
+          ? `<img src="${URL.createObjectURL(file)}" alt="${file.name} preview" class="w-12 h-12 object-cover rounded-md border border-slate-700" onload="URL.revokeObjectURL(this.src)">`
+          : `<span class="w-12 h-12 flex items-center justify-center rounded-md bg-slate-900/70 border border-slate-700 text-lg">📄</span>`;
+        const sizeKb = file.size ? (file.size/1024).toFixed(2) : '0.00';
+        return `<div class="flex items-center gap-3 bg-slate-900/70 px-3 py-2 rounded-lg border border-slate-800/70">
+                  ${preview}
+                  <div class="flex-1 min-w-0">
+                    <p class="text-slate-200 text-sm truncate">${file.name}</p>
+                    <p class="text-slate-500 text-[11px]">${file.type || 'unknown'} • ${sizeKb} KB</p>
+                  </div>
+                  <button data-index="${idx}" class="text-rose-300 hover:text-rose-200 text-xs remove-attachment">Remove</button>
                 </div>`;
       }).join('');
       assistantAttachments.querySelectorAll('.remove-attachment').forEach(btn=>{
         btn.addEventListener('click',(ev)=>{
-          const idx = Number(ev.target.getAttribute('data-index'));
+          const idx = Number(ev.currentTarget.getAttribute('data-index'));
           pendingAttachments.splice(idx,1);
           renderAttachmentList();
         });
       });
     }
 
-    assistantAttachments.innerHTML = '<div class="text-slate-500">No attachments selected.</div>';
+    renderAttachmentList();
 
     document.getElementById('assistant-attach-btn').addEventListener('click', ()=> assistantFileInput.click());
     assistantFileInput.addEventListener('change', (event)=>{
-      pendingAttachments = Array.from(event.target.files || []);
-      renderAttachmentList();
+      addAttachmentsFromFileList(event.target.files || []);
+      assistantFileInput.value = '';
+    });
+
+    ['dragenter','dragover'].forEach(evt=>{
+      assistantDropzone.addEventListener(evt,(event)=>{
+        event.preventDefault();
+        assistantDropzone.classList.add('drop-active');
+      });
+    });
+    ['dragleave','dragend'].forEach(evt=>{
+      assistantDropzone.addEventListener(evt,()=>{
+        assistantDropzone.classList.remove('drop-active');
+      });
+    });
+    assistantDropzone.addEventListener('drop',(event)=>{
+      event.preventDefault();
+      assistantDropzone.classList.remove('drop-active');
+      addAttachmentsFromFileList(event.dataTransfer?.files || []);
+    });
+
+    document.addEventListener('paste',(event)=>{
+      if(assistantModal.getAttribute('aria-hidden') === 'true') return;
+      const items = event.clipboardData?.items || [];
+      const files = [];
+      for(const item of items){
+        if(item.kind === 'file'){
+          const file = item.getAsFile();
+          if(file) files.push(file);
+        }
+      }
+      if(files.length){
+        event.preventDefault();
+        addAttachmentsFromFileList(files);
+      }
     });
 
     document.getElementById('assistant-reset').addEventListener('click', ()=>{
       assistantHistory = [];
       assistantConversation.innerHTML = '<div class="text-slate-400">무엇을 도와드릴까요? (예: “다음 3일 스케줄 요약”)</div>';
       assistantUsage.textContent='';
+      pendingAttachments = [];
+      renderAttachmentList();
     });
 
     async function callAssistant(prompt, attachments){
       const formData = new FormData();
       formData.append('prompt', prompt);
       formData.append('history', JSON.stringify(assistantHistory));
       formData.append('model', assistantModelSelect.value);
       attachments.forEach(file=> formData.append('files', file, file.name));
       const res = await fetch(`${API_BASE}/api/assistant`, { method:'POST', body: formData });
       if(!res.ok){
         const text = await res.text();
         throw new Error(text || 'Assistant call failed');
       }
       const data = await res.json();
       assistantHistory.push({role:'user', content: prompt});
       assistantHistory.push({role:'assistant', content: data.answer});
       assistantUsage.textContent = `Last response model: ${assistantModelSelect.value}`;
       return data.answer;
     }
 
     async function fetchBriefing(){
       modalTitle.textContent = '✨ Daily Briefing';
       modalContent.innerHTML = '생성 중...';
       openModal(briefingModal);
       const payload = {
         current_time: currentSimDate.toISOString(),
         vessel_name: vesselData.name,
         vessel_status: vesselData.status,
         current_voyage: vesselData.currentVoyageId,
         schedule: voyageSchedule,
         weather_windows: weatherWindows.map(w=>({
           start: w.start ? w.start.toISOString?.() || w.start : w.start,
           end: w.end ? w.end.toISOString?.() || w.end : w.end,
           level: w.level,
           waveM: w.waveM,
           windKt: w.windKt,
           visKm: w.visKm
-        }))
+        })),
+        model: assistantModelSelect.value
       };
       try{
         const res = await fetch(`${API_BASE}/api/briefing`, {
           method:'POST',
           headers:{'Content-Type':'application/json'},
           body: JSON.stringify(payload)
         });
         if(!res.ok) throw new Error(await res.text());
         const data = await res.json();
         modalContent.innerHTML = data.briefing.replace(/\n/g,'<br>');
       }catch(err){
         console.error(err);
         const cur = voyageSchedule.find(v=>v.id===vesselData.currentVoyageId);
         const fallback = `현재 시각 ${toLocal(currentSimDate)}.\n진행 항차: ${cur?.id || 'N/A'} / 화물: ${cur?.cargo || 'N/A'} / 상태: ${vesselData.status}.`;
         modalContent.innerHTML = `${fallback.replace(/\n/g,'<br>')}<br><br><span class="text-rose-300">AI Briefing unavailable: ${err.message}</span>`;
       }
     }
 
     async function runRiskScan(){
       const prompt = `다음 일정과 기상창을 기반으로 3가지 위험 시나리오와 대응 권고를 bullet로 정리해줘.\n일정: ${JSON.stringify(voyageSchedule)}\n기상: ${JSON.stringify(weatherWindows)}`;
       setInfo('AI 위험 스캔 실행 중...', 'info');
       try{
         const answer = await callAssistant(prompt, []);
         setInfo(answer.replace(/\n/g,'<br>'), 'warn');
       }catch(err){
@@ -690,58 +812,77 @@
       const q=input.value.trim(); if(!q) return;
       assistantConversation.innerHTML += `<div class="text-right"><span class="bg-purple-800/80 p-2 rounded-lg inline-block">${q}</span></div>`;
       input.value='';
       assistantConversation.scrollTop=assistantConversation.scrollHeight;
       try{
         const ans = await callAssistant(q, pendingAttachments);
         assistantConversation.innerHTML += `<div class="text-left"><span class="bg-slate-800 p-2 rounded-lg inline-block">${ans.replace(/\n/g,'<br>')}</span></div>`;
         assistantConversation.scrollTop=assistantConversation.scrollHeight;
         pendingAttachments = [];
         assistantFileInput.value = '';
         renderAttachmentList();
       }catch(err){
         assistantConversation.innerHTML += `<div class="text-left text-rose-300">${err.message}</div>`;
         assistantConversation.scrollTop=assistantConversation.scrollHeight;
       }
     });
 
     document.getElementById('btn-reset').addEventListener('click', ()=>{
       currentSimDate = new Date("2025-09-28T12:00:00Z");
       vesselData.currentVoyageId = null;
       vesselData.status = "Ready @ MW4";
       setInfo('시뮬레이션 시계가 초기화되었습니다.');
     });
 
     // Marine data functions
-    async function updateMarineForLeg(portName) {
-      // 워커로 오프로드
-      const snap = await fetchMarineAndIOIInWorker(portName);
+    function applyMarineBadge(snap) {
+      const badge = document.getElementById('marineBadge');
+      badge.classList.remove('pill-success','pill-warn','pill-danger');
+      let tone = 'warn';
+      if (snap && typeof snap.ioi === 'number') {
+        if (snap.ioi >= 75) tone = 'success';
+        else if (snap.ioi < 55) tone = 'danger';
+      }
+      badge.classList.add(`pill-${tone}`);
       if (snap && snap.hs != null && snap.windKt != null) {
-        marineBadge.textContent = `Hs: ${snap.hs.toFixed(2)} m · Wind: ${Math.round(snap.windKt)} kt`;
+        badge.textContent = `Hs: ${snap.hs.toFixed(2)} m · Wind: ${snap.windKt.toFixed(2)} kt`;
       } else {
-        marineBadge.textContent = `Marine: n/a`;
+        badge.textContent = `Marine: n/a`;
+      }
+    }
+
+    async function updateMarineForLeg(portName) {
+      const now = Date.now();
+      const cached = marineSnapshotCache.get(portName);
+      if (cached && (now - cached.timestamp) < MARINE_CACHE_TTL_MS) {
+        applyMarineBadge(cached.snap);
+        return cached.snap;
       }
+      // 워커로 오프로드
+      const snap = await fetchMarineAndIOIInWorker(portName);
+      marineSnapshotCache.set(portName, { snap, timestamp: now });
+      applyMarineBadge(snap);
       return snap;
     }
 
     // ===== Worker 생성 (Blob URL) : IOI 계산 + Marine fetch 오프로드 =====
     const workerCode = `
       self.addEventListener('message', async (e) => {
         const { type, payload } = e.data || {};
         if (type === 'marine+ioi') {
           const { port, coords, RULE } = payload;
           try {
             const params = new URLSearchParams({
               latitude: String(coords.lat),
               longitude: String(coords.lon),
               hourly: ['wave_height','wind_speed_10m','swell_wave_period'].join(','),
               timezone: 'auto'
             });
             const url = 'https://marine-api.open-meteo.com/v1/marine?' + params.toString();
             const r = await fetch(url);
             const j = await r.json();
             const idx = 0;
             const hs = j?.hourly?.wave_height?.[idx] ?? null;
             const wsms = j?.hourly?.wind_speed_10m?.[idx] ?? null;
             const sp = j?.hourly?.swell_wave_period?.[idx] ?? null;
             const windKt = wsms != null ? (wsms * 1.94384) : null;
             // IOI 계산 (워커쪽 동일 로직)
diff --git a/openai_gateway.py b/openai_gateway.py
index a46dbf7046d9d902b24c413854dde533462b8562..a6b7dcd7c6ead5a9bbd7a82f2af6195de335af56 100644
--- a/openai_gateway.py
+++ b/openai_gateway.py
@@ -1,235 +1,323 @@
 """OpenAI 연동 FastAPI 백엔드. | FastAPI backend wired with OpenAI."""
 
 from __future__ import annotations
 
 import base64
 import io
 import json
 import logging
 import os
-from typing import Iterable, List, Literal, Sequence
+from typing import Any, Iterable, List, Literal, Sequence
 
 from fastapi import FastAPI, File, Form, HTTPException, UploadFile
 from fastapi.middleware.cors import CORSMiddleware
 from openai import AsyncOpenAI
-from openai.types.chat import ChatCompletion
 from pydantic import BaseModel, ConfigDict, Field
 from PyPDF2 import PdfReader
 
-
 LOGGER = logging.getLogger(__name__)
 
 
 class LogiBaseModel(BaseModel):
     """로지스틱 도메인 공통 베이스 모델. | Common logistics base model."""
 
     model_config = ConfigDict(extra="forbid", populate_by_name=True)
 
 
 class ChatMessage(LogiBaseModel):
     """사용자/AI 메시지 구조. | Chat message schema."""
 
     role: Literal["user", "assistant", "system"]
     content: str = Field(..., max_length=6000)
 
 
 class BriefingRequest(LogiBaseModel):
     """일일 브리핑 요청 본문. | Daily briefing payload."""
 
     current_time: str
     vessel_name: str
     vessel_status: str
     current_voyage: str | None = None
     schedule: List[dict] = Field(default_factory=list)
     weather_windows: List[dict] = Field(default_factory=list)
+    model: str = Field(default="gpt-4.1-mini", max_length=64)
 
 
 class BriefingResponse(LogiBaseModel):
     """일일 브리핑 응답. | Daily briefing response."""
 
     briefing: str
 
 
 class AssistantResponse(LogiBaseModel):
     """AI 어시스턴트 응답. | AI assistant response."""
 
     answer: str
 
 
 _async_client: AsyncOpenAI | None = None
 
 
 def _require_client() -> AsyncOpenAI:
     """OpenAI 클라이언트를 생성. | Build an OpenAI client."""
 
     api_key = os.getenv("OPENAI_API_KEY")
     if not api_key:
-        raise HTTPException(status_code=500, detail="OPENAI_API_KEY is not configured")
+        error_message = "OPENAI_API_KEY is not configured"
+        raise HTTPException(status_code=500, detail=error_message)
     global _async_client
     if _async_client is None:
         _async_client = AsyncOpenAI(api_key=api_key)
     return _async_client
 
 
 def _pdf_to_text(payload: bytes) -> str:
     """PDF를 텍스트로 추출. | Extract text from PDF."""
 
     reader = PdfReader(io.BytesIO(payload))
     text_chunks: List[str] = []
     for page in reader.pages:
         snippet = page.extract_text() or ""
         text_chunks.append(snippet)
     return "\n".join(text_chunks)
 
 
 def _image_to_base64(file: UploadFile, payload: bytes) -> dict:
     """이미지를 base64로 인코딩. | Encode image to base64."""
 
-    data_url = f"data:{file.content_type};base64,{base64.b64encode(payload).decode('utf-8')}"
-    return {"type": "input_image", "image_url": data_url}
+    data_url = "data:{media};base64,{payload}".format(
+        media=file.content_type,
+        payload=base64.b64encode(payload).decode("utf-8"),
+    )
+    return {"type": "input_image", "image_url": {"url": data_url}}
 
 
-def _build_user_content(prompt: str, files: Iterable[UploadFile], raw_payloads: List[bytes]) -> str:
+def _build_user_content(
+    prompt: str, files: Iterable[UploadFile], raw_payloads: List[bytes]
+) -> List[dict[str, Any]]:
     """사용자 메시지 콘텐츠 구성. | Compose user content payload."""
 
-    content_parts = [prompt]
+    content: List[dict[str, Any]] = [{"type": "text", "text": prompt}]
     for idx, file in enumerate(files):
         data = raw_payloads[idx]
+        filename = file.filename or f"attachment-{idx+1}"
         if file.content_type and file.content_type.startswith("image/"):
-            # For images, we'll include a reference in the text
-            content_parts.append(f"\n[첨부 이미지: {file.filename}]")
-        elif (file.content_type == "application/pdf") or file.filename.lower().endswith(".pdf"):
+            content.append(
+                {
+                    "type": "text",
+                    "text": f"[이미지 첨부: {filename}]",
+                }
+            )
+            content.append(_image_to_base64(file, data))
+            continue
+
+        is_pdf_content = file.content_type == "application/pdf"
+        if is_pdf_content or filename.lower().endswith(".pdf"):
             pdf_text = _pdf_to_text(data)[:8000]
-            descriptor = f"\n[첨부 PDF: {file.filename}]\n"
-            content_parts.append(descriptor + pdf_text)
-        else:
-            try:
-                decoded = data.decode("utf-8")
-            except UnicodeDecodeError:
-                decoded = base64.b64encode(data).decode("utf-8")
-                decoded = f"[base64-encoded attachment]\n{decoded[:6000]}"
-            content_parts.append(f"\n[첨부 파일: {file.filename}]\n{decoded[:8000]}")
-    return "\n".join(content_parts)
-
-
-def _extract_output_text(response: ChatCompletion) -> str:
+            descriptor = f"[PDF 첨부: {filename}]\n{pdf_text}"
+            content.append(
+                {
+                    "type": "text",
+                    "text": descriptor,
+                }
+            )
+            continue
+
+        try:
+            decoded = data.decode("utf-8")
+        except UnicodeDecodeError:
+            decoded = base64.b64encode(data).decode("utf-8")
+            decoded = f"[base64-encoded attachment]\n{decoded[:6000]}"
+        content.append(
+            {
+                "type": "text",
+                "text": f"[파일 첨부: {filename}]\n{decoded[:8000]}",
+            }
+        )
+
+    return content
+
+
+def _extract_output_text(response: Any) -> str:
     """Chat Completion 결과에서 텍스트 추출. | Extract text from Chat Completion."""
 
+    outputs = getattr(response, "output", None)
+    if outputs:
+        texts: List[str] = []
+        for item in outputs:
+            if getattr(item, "type", None) != "message":
+                continue
+            message = getattr(item, "message", None)
+            if not message:
+                continue
+            for block in getattr(message, "content", []) or []:
+                if getattr(block, "type", None) == "text":
+                    text_value = getattr(block, "text", "")
+                    if text_value:
+                        texts.append(text_value)
+        if texts:
+            return "\n".join(texts)
+
     try:
         return response.choices[0].message.content
     except (AttributeError, IndexError, KeyError):
         return "Error: Could not extract response text"
 
 
-async def _call_openai(messages: List[dict], *, model: str) -> ChatCompletion:
+async def _call_openai(messages: List[dict[str, Any]], *, model: str) -> Any:
     """OpenAI Responses API 호출. | Invoke OpenAI Responses API."""
 
     client = _require_client()
-    return await client.chat.completions.create(model=model, messages=messages)
+    return await client.responses.create(model=model, input=messages)
 
 
-def _build_history(messages: Sequence[ChatMessage]) -> List[dict]:
+def _build_history(messages: Sequence[ChatMessage]) -> List[dict[str, Any]]:
     """Chat Completion용 메시지 배열 구성. | Build chat completion messages."""
 
-    history: List[dict] = []
+    history: List[dict[str, Any]] = []
     for item in messages:
-        history.append({
-            "role": item.role,
-            "content": item.content
-        })
+        history.append(
+            {
+                "role": item.role,
+                "content": [
+                    {"type": "text", "text": item.content},
+                ],
+            }
+        )
     return history
 
 
 app = FastAPI(title="HVDC Logistics AI Gateway", version="1.0.0")
 app.add_middleware(
     CORSMiddleware,
     allow_origins=["*"],
     allow_credentials=True,
     allow_methods=["*"],
     allow_headers=["*"],
 )
 
 
 @app.get("/health")
 async def healthcheck() -> dict:
     """헬스체크. | Service health check."""
 
     return {"status": "ok"}
 
 
 @app.post("/api/assistant", response_model=AssistantResponse)
 async def run_assistant(
     prompt: str = Form(..., max_length=4000),
     history: str = Form("[]"),
     files: List[UploadFile] | None = File(default=None),
     model: str = Form("gpt-4.1-mini"),
 ) -> AssistantResponse:
     """어시스턴트 호출. | Execute assistant call."""
 
     try:
         raw_history = json.loads(history)
-        history_messages = [ChatMessage.model_validate(item) for item in raw_history]
-    except (json.JSONDecodeError, TypeError, ValueError) as exc:  # pragma: no cover - validation
-        raise HTTPException(status_code=400, detail=f"Invalid history payload: {exc}") from exc
+        history_messages: List[ChatMessage] = []
+        for item in raw_history:
+            history_messages.append(ChatMessage.model_validate(item))
+    except (
+        json.JSONDecodeError,
+        TypeError,
+        ValueError,
+    ) as exc:  # pragma: no cover - validation
+        raise HTTPException(
+            status_code=400, detail=f"Invalid history payload: {exc}"
+        ) from exc
 
     attachments = list(files or [])
     payloads: List[bytes] = []
     for file in attachments:
         payloads.append(await file.read())
 
     messages = _build_history(history_messages)
-    messages.append({"role": "user", "content": _build_user_content(prompt, attachments, payloads)})
+    messages.append(
+        {
+            "role": "user",
+            "content": _build_user_content(prompt, attachments, payloads),
+        }
+    )
 
     try:
         response = await _call_openai(messages, model=model)
     except Exception as exc:  # pragma: no cover - network failure
         LOGGER.exception("OpenAI call failed")
         raise HTTPException(status_code=502, detail=str(exc)) from exc
 
     return AssistantResponse(answer=_extract_output_text(response))
 
 
 @app.post("/api/briefing", response_model=BriefingResponse)
 async def generate_briefing(payload: BriefingRequest) -> BriefingResponse:
     """일일 브리핑 생성. | Create a daily briefing."""
 
-    schedule_summary = json.dumps(payload.schedule, ensure_ascii=False, indent=2)
-    weather_summary = json.dumps(payload.weather_windows, ensure_ascii=False, indent=2)
-    prompt = (
-        "당신은 해상 물류 관제 전문가입니다. 아래 데이터를 참고하여 200자 내외의 한국어 일일 브리핑을 작성하세요."
-        "\n- 현재 시각: {time}\n- 선박명: {vessel}\n- 현재 항차: {voyage}\n- 선박 상태: {status}\n"
-        "- 전체 일정: {schedule}\n- 기상 윈도우: {weather}\n"
-        "브리핑은 핵심 일정, 위험, 권고사항을 bullet로 정리하세요."
-    ).format(
+    schedule_summary = json.dumps(
+        payload.schedule,
+        ensure_ascii=False,
+        indent=2,
+    )
+    weather_summary = json.dumps(
+        payload.weather_windows,
+        ensure_ascii=False,
+        indent=2,
+    )
+    prompt_template = (
+        "당신은 해상 물류 관제 전문가입니다. "
+        "아래 데이터를 참고하여 200자 내외의 한국어 일일 브리핑을 작성하세요."
+        "\n- 현재 시각: {time}"
+        "\n- 선박명: {vessel}"
+        "\n- 현재 항차: {voyage}"
+        "\n- 선박 상태: {status}"
+        "\n- 전체 일정: {schedule}"
+        "\n- 기상 윈도우: {weather}"
+        "\n브리핑은 핵심 일정, 위험, 권고사항을 bullet로 정리하세요."
+    )
+    prompt = prompt_template.format(
         time=payload.current_time,
         vessel=payload.vessel_name,
         voyage=payload.current_voyage or "N/A",
         status=payload.vessel_status,
         schedule=schedule_summary,
         weather=weather_summary,
     )
 
     try:
         response = await _call_openai(
             [
                 {
                     "role": "system",
-                    "content": "당신은 HVDC 프로젝트 물류 전문가입니다. 일일 브리핑을 한국어로 작성하세요.",
+                    "content": [
+                        {
+                            "type": "text",
+                            "text": (
+                                "당신은 HVDC 프로젝트 물류 전문가입니다. "
+                                "일일 브리핑을 한국어로 작성하세요."
+                            ),
+                        }
+                    ],
                 },
                 {
                     "role": "user",
-                    "content": prompt,
+                    "content": [
+                        {
+                            "type": "text",
+                            "text": prompt,
+                        }
+                    ],
                 },
             ],
             model=payload.model,
         )
     except Exception as exc:  # pragma: no cover - network failure
         LOGGER.exception("OpenAI call failed")
         raise HTTPException(status_code=502, detail=str(exc)) from exc
 
     return BriefingResponse(briefing=_extract_output_text(response))
 
 
 if __name__ == "__main__":
     import uvicorn
-    uvicorn.run(app, host="0.0.0.0", port=8000)
\ No newline at end of file
+
+    uvicorn.run(app, host="0.0.0.0", port=8000)
