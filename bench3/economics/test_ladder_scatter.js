const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const path=require('node:path');
const dir=path.resolve(process.argv[2]||__dirname);
const chart=require(dir+'/ladder_scatter.js');
const context={window:{}};vm.runInNewContext(fs.readFileSync(dir+'/ladder_data.js','utf8'),context);
const data=context.window.LADDER_DATA,before=JSON.stringify(data);
const all=chart.select(data);
assert.equal(all.length,32);
assert.equal(new Set(all.map(p=>p.key)).size,32);
assert.equal(all.reduce((n,p)=>n+p.source.runs,0),2240);
for(const point of all){
  const original=data.configs.find(c=>c.starting_route===point.route.id&&c.effort===point.effort);
  assert.equal(point.cost,original.attempt*100);
  assert.equal(point.seconds,original.latency,'All-task points must use pooled measured medians');
  assert.equal(point.source,original);
}
let checked=0;
for(const task of data.tasks)for(const effort of ['low','high']){
  const rows=chart.select(data,task.code,effort);
  assert.equal(rows.length,16);assert.equal(rows.reduce((n,p)=>n+p.source.runs,0),160);
  for(const point of rows){
    const original=data.cells.find(c=>c.starting_route===point.route.id&&c.task===task.code&&c.effort===effort);
    assert.equal(point.cost,original.attempt*100);assert.equal(point.seconds,original.latency);checked++;
  }
  const active=chart.select(data,task.code,effort,'active');
  assert.ok(active.every(p=>p.seconds===p.source.modelSeconds));
  for(const width of [280,360,768,1180]){
    const g=chart.geometry(rows,width);
    assert.equal(g.width,width);assert.equal(g.xTicks[0],0);
    assert.equal(g.yTicks[0],.1);assert.equal(g.yTicks.at(-1),100000);
    for(const p of g.positions){
      assert.ok(p.x>=g.frame.left+12&&p.x<=g.frame.right-12);
      assert.ok(p.y>=g.frame.top+12&&p.y<=g.frame.bottom-12);
      assert.ok(Number.isFinite(p.x)&&Number.isFinite(p.y));
    }
    assert.ok(!/NaN|Infinity|undefined/.test(chart.plot(rows,width,rows[0].key)));
    assert.ok(width>=520||g.xTicks.length<=4,'Reduce time ticks on narrow screens');
  }
}
assert.equal(checked,224);
assert.equal(chart.select(null).length,0);
assert.equal(chart.select(data,'not-a-task').length,0);
assert.equal(chart.select(data,'all','not-an-effort').length,0);
assert.equal(chart.select(data,'all','all','not-a-time').length,0);
assert.match(chart.plot([],360,null),/No measured workflows/);
assert.match(chart.detail(null,'wall'),/Earlier estimates are not substituted/);
const incomplete={routes:[{id:'a',name:'<script>alert(1)</script>',sub:'vendor'}],configs:[
  {starting_route:'a',effort:'low',runs:0,attempt:999,latency:3},
  {starting_route:'a',effort:'high',runs:1,passes:1,attempt:2,latency:4,modelSeconds:3,retries:0,upgrades:0}]};
assert.equal(chart.select(incomplete).length,1);
const selected=chart.select(incomplete)[0];
assert.match(chart.detail(selected,'wall'),/&lt;script&gt;/);
assert.ok(!chart.plot([selected],360,selected.key).includes('<script>'));
assert.match(chart.detail({...selected,source:{...selected.source,missingUsageReceipts:1}},'wall'),/cost is incomplete/);
assert.equal(JSON.stringify(data),before,'The chart must not mutate benchmark data or frozen plans');
console.log('Cost/time chart checks passed: all 224 measured cells, 32 separate settings, exact units and medians, active time, empty data, small screens, safe labels, and immutable evidence.');
