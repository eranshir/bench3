/* Measured ladder display only. No training estimates or provider requests. */
(function(root){
  'use strict';
  const escape=value=>String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const money=value=>'$'+value.toLocaleString('en-US',{minimumFractionDigits:2,maximumFractionDigits:2});
  const seconds=value=>value.toFixed(1)+' s';
  const range=(values,format)=>values?values.map(v=>v==null?'unbounded':format(v)).join('–'):'not available';
  const color=route=>/^#[0-9a-f]{6}$/i.test(route.color||'')?route.color:'var(--cyan)';

  function select(data,task='all',effort='all',time='wall'){
    if(!data||!['all','low','high'].includes(effort)||!['wall','active'].includes(time))return [];
    const routes=new Map((data.routes||[]).map(r=>[r.id,r]));
    const source=task==='all'?data.configs||[]:(data.cells||[]).filter(c=>c.task===task);
    return source.filter(s=>routes.has(s.starting_route)&&['low','high'].includes(s.effort)&&
      (effort==='all'||s.effort===effort)&&s.runs>0&&Number.isFinite(s.attempt)&&s.attempt>0&&
      Number.isFinite(time==='wall'?s.latency:s.modelSeconds)&&(time==='wall'?s.latency:s.modelSeconds)>=0)
      .map(s=>({key:s.starting_route+'|'+s.effort,route:routes.get(s.starting_route),effort:s.effort,
        cost:s.attempt*100,seconds:time==='wall'?s.latency:s.modelSeconds,source:s}));
  }

  function geometry(points,width=960){
    width=Math.max(280,Number.isFinite(width)?width:960);
    const height=width<520?400:460,frame={left:78,right:width-22,top:26,bottom:height-64};
    const maximum=Math.max(1,...points.map(p=>p.seconds))*1.12;
    const raw=maximum/(width<520?3:5),power=10**Math.floor(Math.log10(raw));
    const step=[1,2,5,10].map(n=>n*power).find(n=>n>=raw);
    const xMax=Math.ceil(maximum/step)*step;
    const low=Math.min(.1,...points.map(p=>p.cost)),high=Math.max(100000,...points.map(p=>p.cost));
    const minExp=Math.floor(Math.log10(low)),maxExp=Math.ceil(Math.log10(high));
    const yTicks=Array.from({length:maxExp-minExp+1},(_,i)=>10**(minExp+i));
    const xTicks=Array.from({length:Math.round(xMax/step)+1},(_,i)=>i*step);
    // Inset the data range so marker centers do not sit on the frame.
    const positions=points.map(p=>({...p,
      x:frame.left+12+p.seconds/xMax*(frame.right-frame.left-24),
      y:frame.bottom-12-(Math.log10(p.cost)-minExp)/(maxExp-minExp)*(frame.bottom-frame.top-24)}));
    return {width,height,frame,xMax,xTicks,yTicks,minExp,maxExp,positions};
  }

  function plot(points,width,selectedKey,time='wall'){
    const g=geometry(points,width),f=g.frame;
    const x=value=>f.left+12+value/g.xMax*(f.right-f.left-24);
    const y=value=>f.bottom-12-(Math.log10(value)-g.minExp)/(g.maxExp-g.minExp)*(f.bottom-f.top-24);
    const selected=points.find(p=>p.key===selectedKey);
    let svg=`<svg class="ladder-scatter-svg" viewBox="0 0 ${g.width} ${g.height}" role="group" aria-labelledby="scatter-svg-title scatter-svg-desc"><title id="scatter-svg-title">Measured ladder cost versus time</title><desc id="scatter-svg-desc">Each point is one starting route and effort. Cost uses a logarithmic scale. Time uses a linear scale. Select a point or its model below for exact values. Circles show low effort. Diamonds show high effort.</desc>`;
    svg+=`<rect class="scatter-frame" x="${f.left}" y="${f.top}" width="${f.right-f.left}" height="${f.bottom-f.top}"/>`;
    for(const value of g.yTicks){
      const yy=y(value),label=value<1?'$0.10':value>=1000?'$'+value/1000+'K':'$'+value;
      svg+=`<path class="scatter-grid" d="M${f.left},${yy}H${f.right}"/><text class="scatter-tick" x="${f.left-10}" y="${yy+4}" text-anchor="end">${label}</text>`;
    }
    for(const value of g.xTicks){
      const xx=x(value);
      svg+=`<path class="scatter-grid" d="M${xx},${f.top}V${f.bottom}"/><text class="scatter-tick" x="${xx}" y="${f.bottom+23}" text-anchor="middle">${Number(value.toFixed(2))}</text>`;
    }
    svg+=`<text class="scatter-axis-title" x="${(f.left+f.right)/2}" y="${g.height-12}" text-anchor="middle">Median ${time==='active'?'active':'wall'} time · seconds</text><text class="scatter-axis-title" transform="translate(18 ${(f.top+f.bottom)/2}) rotate(-90)" text-anchor="middle">Cost / 100,000 original tasks · USD</text>`;
    for(const p of g.positions.slice().sort((a,b)=>(a.key===selectedKey)-(b.key===selectedKey))){
      const chosen=p.key===selectedKey,related=!selected||selected.route.id===p.route.id;
      const title=`${p.route.name} · ${p.route.sub} · ${p.effort} effort: ${money(p.cost)} per 100,000; ${seconds(p.seconds)}; ${p.source.passes}/${p.source.runs} passed`;
      svg+=`<g class="scatter-point${chosen?' is-selected':''}${related?'':' is-muted'}" data-point="${escape(p.key)}" role="button" tabindex="0" aria-pressed="${chosen}" aria-label="${escape(title)}" style="--point-color:${color(p.route)}"><title>${escape(title)}</title><circle class="scatter-hit" cx="${p.x}" cy="${p.y}" r="15"/>`;
      if(chosen)svg+=`<circle class="scatter-selection" cx="${p.x}" cy="${p.y}" r="14"/>`;
      svg+=p.effort==='low'?`<circle class="scatter-mark" cx="${p.x}" cy="${p.y}" r="7"/>`:
        `<path class="scatter-mark" d="M${p.x},${p.y-9}l9,9l-9,9l-9,-9Z"/>`;
      svg+='</g>';
    }
    if(!points.length)svg+=`<text class="scatter-axis-title" x="${(f.left+f.right)/2}" y="${(f.top+f.bottom)/2}" text-anchor="middle">No measured workflows for these filters</text>`;
    return svg+'</svg>';
  }

  function detail(point,time){
    if(!point)return '<p>No measured workflows for these filters. Earlier estimates are not substituted.</p>';
    const s=point.source;
    return `<div class="scatter-selected-name"><strong>${escape(point.route.name)}</strong><span>${escape(point.route.sub)} · ${point.effort} effort</span></div><div class="scatter-selected-values"><div><span>Cost / 100K original tasks</span><strong>${money(point.cost)}</strong><small>95% cost interval: ${range(s.attemptCI100k,money)}</small></div><div><span>Median ${time==='active'?'active':'wall'} time</span><strong>${seconds(point.seconds)}</strong><small>All reached attempts and Aegis retries</small></div><div><span>Measured passes</span><strong>${s.passes}/${s.runs}</strong><small>95% pass interval: ${range(s.passCI,v=>v.toFixed(1)+'%')}</small></div></div><p>${s.retries} enforced ${s.retries===1?'retry':'retries'} · ${s.upgrades} ${s.upgrades===1?'upgrade':'upgrades'}${s.missingUsageReceipts?` · ${s.missingUsageReceipts} missing usage receipt; cost is incomplete`:''}</p>`;
  }

  function mount(doc,data){
    const get=id=>doc.querySelector('#'+id),task=get('scatter-task'),effort=get('scatter-effort'),time=get('scatter-time');
    let current=data,selectedKey=null;
    task.innerHTML='<option value="all">All seven tasks · equal mix</option>'+(data.tasks||[]).map(t=>`<option value="${escape(t.code)}">${escape(t.name)}</option>`).join('');
    task.value='all';effort.value='all';time.value='wall';
    function render(){
      const points=select(current,task.value,effort.value,time.value);
      if(!points.some(p=>p.key===selectedKey))selectedKey=points.slice().sort((a,b)=>a.cost-b.cost)[0]?.key||null;
      const chosen=points.find(p=>p.key===selectedKey);
      const width=get('scatter-plot').getBoundingClientRect?.().width||960;
      get('scatter-plot').innerHTML=plot(points,width,selectedKey,time.value);
      get('scatter-detail').innerHTML=detail(chosen,time.value);
      const shownRoutes=(current.routes||[]).filter(r=>points.some(p=>p.route.id===r.id));
      get('scatter-legend').innerHTML=shownRoutes.map(r=>`<button type="button" data-route="${escape(r.id)}" aria-pressed="${chosen?.route.id===r.id}" style="--point-color:${color(r)}"><i aria-hidden="true"></i><span>${escape(r.name)}<small>${escape(r.sub)}</small></span></button>`).join('');
      get('scatter-summary').textContent=`${points.length} measured points · ${points.reduce((n,p)=>n+p.source.runs,0).toLocaleString()} original workflows · ${task.value==='all'?'each point uses all seven tasks':'each point uses the selected task'}. Both efforts stay separate. Lower and further left means lower cost and less time.`;
    }
    function choose(key){
      selectedKey=key;render();
      const target=get('scatter-plot').querySelector?.(`[data-point="${key}"]`);
      target?.focus?.({preventScroll:true});
    }
    for(const control of [task,effort,time])control.addEventListener('change',render);
    get('scatter-plot').addEventListener('click',event=>{
      const key=event.target.closest('[data-point]')?.dataset.point;if(key)choose(key);
    });
    get('scatter-plot').addEventListener('keydown',event=>{
      if(!['Enter',' '].includes(event.key))return;
      const key=event.target.closest('[data-point]')?.dataset.point;
      if(key){event.preventDefault();choose(key);}
    });
    get('scatter-legend').addEventListener('click',event=>{
      const id=event.target.closest('[data-route]')?.dataset.route;
      const point=select(current,task.value,effort.value,time.value).find(p=>p.route.id===id);
      if(point)choose(point.key);
    });
    if(typeof root.ResizeObserver==='function')new root.ResizeObserver(render).observe(get('scatter-plot'));
    render();return {update(value){current=value;render();}};
  }
  const api={select,geometry,plot,detail,mount};
  if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.LADDER_SCATTER=api;
})(typeof window==='undefined'?globalThis:window);
