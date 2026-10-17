/* Display-only attachment. It cannot alter frozen plans or benchmark grades. */
(function(root){
  'use strict';
  function wilson(passes,runs){
    if(!runs)return null;
    const z=1.959963984540054,p=passes/runs,d=1+z*z/runs;
    const c=(p+z*z/(2*runs))/d,h=z*Math.sqrt(p*(1-p)/runs+z*z/(4*runs*runs))/d;
    return [100*Math.max(0,c-h),100*Math.min(1,c+h)];
  }
  function attach(data,ladder){
    const cells=new Map((ladder?.cells||[]).map(c=>[[c.starting_route,c.task,c.effort].join('|'),c]));
    for(const task of data.tasks)for(const [index,route] of data.routes.entries()){
      const parts=[];
      for(const effort of ['low','high']){
        const result=cells.get([route.id,task.code,effort].join('|'))||null;
        parts.push(result);
        for(const policy of ['base','withAegis']){
          const row=task.byEffort[effort][policy][index];
          row.measuredResult=result;
          row.measuredLadder=result?.runs ? result.attempt : null;
        }
      }
      const runs=parts.reduce((n,s)=>n+(s?.runs||0),0),passes=parts.reduce((n,s)=>n+(s?.passes||0),0);
      const all=runs ? {runs,passes,passRate:100*passes/runs,passCI:wilson(passes,runs),
        plannedRuns:20,attempt:parts.reduce((n,s)=>n+(s?.runs ? s.runs*s.attempt : 0),0)/runs,
        attemptCI100k:null,stages:null} : null;
      for(const policy of ['base','withAegis']){
        const row=task.byEffort.all[policy][index];
        row.measuredResult=all;row.measuredLadder=all?.attempt??null;
      }
    }
    return data;
  }
  const api={attach,wilson};
  if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.LADDER_REPORT=api;
})(typeof window==='undefined'?globalThis:window);
