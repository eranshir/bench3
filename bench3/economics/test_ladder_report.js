const assert=require('node:assert/strict');
const {attach,wilson}=require('./ladder_report.js');
const data={routes:[{id:'source'}],tasks:[{code:'task',byEffort:{}}]};
for(const effort of ['low','high','all'])data.tasks[0].byEffort[effort]={
  base:[{attempt:999,passes:10,runs:10,ladder:123}],withAegis:[{attempt:1000,passes:10,runs:10,ladder:123}]};
attach(data,null);
assert.equal(data.tasks[0].byEffort.low.base[0].measuredLadder,null);
const cells=[{starting_route:'source',task:'task',effort:'low',runs:2,passes:1,attempt:3},
  {starting_route:'source',task:'task',effort:'high',runs:1,passes:1,attempt:9}];
attach(data,{cells});
const low=data.tasks[0].byEffort.low.base[0],all=data.tasks[0].byEffort.all.base[0];
assert.equal(low.measuredLadder,3);assert.equal(low.attempt,999);assert.equal(low.ladder,123);
assert.equal(all.measuredLadder,5);assert.equal(all.measuredResult.runs,3);assert.equal(all.measuredResult.passes,2);
assert.equal(data.tasks[0].byEffort.high.withAegis[0].measuredLadder,9);
assert.ok(wilson(10,10)[0]>72&&wilson(10,10)[0]<73);
assert.equal(wilson(0,0),null);
cells[0].runs=0;cells[0].passes=0;cells[0].attempt=null;attach(data,{cells});
assert.equal(data.tasks[0].byEffort.low.base[0].measuredLadder,null);
assert.equal(data.tasks[0].byEffort.all.base[0].measuredLadder,9);
console.log('Measured ladder display checks passed: no invented observations, effort weighting, units, pass intervals, and estimate isolation.');
