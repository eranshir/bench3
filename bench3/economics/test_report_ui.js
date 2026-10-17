/* DOM-stub unit test, not a browser layout or visual test. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const reportDir = path.resolve(process.argv[2] || __dirname);
const hybrid = require(reportDir+'/hybrid_cost.js');
const ladderReport=require(reportDir+'/ladder_report.js');
const html = fs.readFileSync(reportDir+'/report.html','utf8');
// querySelector('#1017-...') is invalid CSS although it is a legal HTML ID.
// The DOM stub must not silently accept this browser syntax error.
for (const selector of html.matchAll(/querySelector\(['"](#\d[^'"]*)['"]\)/g)) {
  assert.fail('Numeric-leading ID used as an unescaped CSS selector: '+selector[1]);
}
assert.match(html.match(/\.fade-in\s*\{([^}]+)\}/)[1], /opacity:\s*1/,
  'Report content must remain visible if page initialization fails');
const elements = new Map();
class Element {
  constructor() { this.dataset={};this.handlers={};this.value='';this.classList={add(){}}; }
  addEventListener(name,fn) {this.handlers[name]=fn;}
  setAttribute(name,value) {this[name]=value;}
  closest() {return this;}
}
const get = key => {if(!elements.has(key))elements.set(key,new Element());return elements.get(key);};
const buttonGroups = new Map();
for(const id of ['metric-switch','policy-switch','effort-switch','task-filter']) {
  const content=html.match(new RegExp('<div[^>]*id="'+id+'"[^>]*>([\\s\\S]*?)</div>'))[1];
  const buttons=[...content.matchAll(/<button([^>]*)>/g)].map(match=>{
    const button=new Element();
    for(const attr of match[1].matchAll(/data-(\w+)="([^"]*)"/g))button.dataset[attr[1]]=attr[2];
    return button;
  });
  buttonGroups.set('#'+id+' button',buttons);
}
const context={window:{HYBRID_COST:hybrid},HYBRID_COST:hybrid,LADDER_REPORT:ladderReport,
  document:{querySelector:get,querySelectorAll:key=>buttonGroups.get(key)||[],createElement:()=>new Element(),head:{appendChild(){}}},
  IntersectionObserver:class {observe(){}unobserve(){}},setInterval(){},setTimeout(){},Blob,URL};
vm.createContext(context);
vm.runInContext(fs.readFileSync(reportDir+'/report_data.js','utf8'),context);
vm.runInContext(fs.readFileSync(reportDir+'/ladder_data.js','utf8'),context);
for(const script of html.matchAll(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/g))if(script[1].trim())vm.runInContext(script[1],context);
const click=(id,key,value)=>{
  const button=buttonGroups.get('#'+id+' button').find(button=>button.dataset[key]===value);
  get('#'+id).handlers.click({target:button});
};
click('metric-switch','metric','hybrid');
assert.equal(get('#hybrid-method').hidden,false);
assert.match(get('#matrix-title').textContent,/Aegis-first hybrid/);
assert.ok(buttonGroups.get('#policy-switch button').find(button=>button.dataset.policy==='withAegis').disabled);
assert.match(get('#hybrid-candidates').textContent,/140 objective base tasks/);
assert.match(get('#policy-context').textContent,/includes failed attempts and retries/);
click('effort-switch','effort','high');
assert.match(get('#route-bars').innerHTML,/n=10|Pending|n=[1-9]/);
click('metric-switch','metric','ladder');
assert.equal(get('#ladder-detail').hidden,false);
assert.match(get('#ladder-body').innerHTML,/final fallback/);
assert.match(get('#matrix-title').textContent,/Aegis cost ladder/);
click('metric-switch','metric','measuredLadder');
assert.equal(get('#linked-ladder').hidden,false);
assert.match(html,/Median active time/);
assert.match(get('#linked-recovery').href,/recovery_audit\.json$/);
if(context.window.LADDER_DATA.finalAuditAvailable){
  assert.equal(get('#linked-recovery').hidden,false);
  assert.match(get('#linked-message').textContent,/audit reports are available/);
}
assert.match(get('#matrix-title').textContent,/Measured ladder cost/);
assert.match(get('#policy-context').textContent,/fresh calls only/);
assert.match(get('#ladder-detail-title').textContent,/Measured ladder paths/);
assert.ok(!get('#task-body').innerHTML.includes('Estimate · Aegis retries included'));
click('metric-switch','metric','success');
assert.equal(get('#hybrid-method').hidden,true);
assert.equal(get('#ladder-detail').hidden,true);
assert.equal(buttonGroups.get('#policy-switch button').find(button=>button.dataset.policy==='withAegis').disabled,false);
click('policy-switch','policy','withAegis');
click('task-filter','category','tool-loop');
assert.ok(!get('#task-body').innerHTML.includes('Long tiling proof'));
let cells=0;
const data=context.window.REPORT_DATA;
for(const task of data.tasks)for(const effort of ['low','high'])for(const result of task.byEffort[effort].base){
  if(result.ladder==null)continue;
  assert.ok(result.ladder<=result.hybrid+1e-10,'Greedy levels must not add expected cost');
  assert.ok(result.ladder>=result.aegisStageCost-1e-10,'Never omit the first stage or its retries');
  assert.ok(Math.abs(result.ladder-result.ladderPlan.reduce((sum,s)=>sum+s.contribution,0))<1e-10);
  assert.ok(data.hybridMethod.qualifyingRoutes.includes(result.ladderPlan.at(-1).id));
  cells++;
}
assert.ok(cells>0,'Check policy paths against real report observations');
console.log('Report interaction unit checks passed: initial render, Aegis-first hybrid, estimated and measured ladder paths, effort switch, policy isolation, task filter.');
