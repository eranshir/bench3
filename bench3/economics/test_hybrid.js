const assert = require('node:assert/strict');
const { derive, csv, greedyLadder } = require('./hybrid_cost.js');

function fixture() {
  const row = (cost, passes = 10, runs = 10) => ({ attempt: cost, passes, runs });
  const data = { routes: ['cheap', 'fallback', 'expensive'].map(id => ({id, name:id, sub:'test'})),
    campaign: {repetitions:10, configs:[]}, tasks: [] };
  for (const code of ['task-a', 'task-b']) {
    const byEffort = {};
    for (const effort of ['all', 'low', 'high']) {
      const base = [row(2,8), row(10), row(20)];
      byEffort[effort] = { base, withAegis: base.map((s,i) => ({...s,
        attempt:i === 0 ? 3 : s.attempt, passes:i === 0 ? 9 : 10,
        retryCount:s.runs-s.passes})) };
    }
    data.tasks.push({code, byEffort});
  }
  return data;
}

let data = derive(fixture());
let cell = data.tasks[0].byEffort.low.base[0];
assert.ok(Math.abs(cell.weighted - 3.6) < 1e-12);
assert.ok(Math.abs(cell.sequentialEscalation - 4) < 1e-12);
assert.ok(Math.abs(cell.hybrid - 4) < 1e-12); // 3 includes retries, then 0.1*10.
assert.ok(Math.abs(cell.ladder - 4) < 1e-12);
assert.equal(cell.hybridFallback.id, 'fallback');
assert.deepEqual(data.hybridMethod.qualifyingRoutes, ['fallback','expensive']);
assert.equal(data.tasks[0].byEffort.low.withAegis[0].hybrid, cell.hybrid);

data = fixture();
data.tasks[1].byEffort.high.base[1].runs = 9;
data.tasks[1].byEffort.high.base[1].passes = 9;
derive(data);
assert.equal(data.tasks[0].byEffort.low.base[0].hybridFallback.id, 'expensive');

data = fixture();
data.tasks[0].byEffort.low.base[0].passes = 0;
derive(data);
assert.equal(data.tasks[0].byEffort.low.base[0].weighted, 10);
assert.equal(data.tasks[0].byEffort.low.base[1].hybrid, 10);

data = fixture();
for (const task of data.tasks) for (const effort of ['low','high']) {
  task.byEffort[effort].base[1].passes = 9;
  task.byEffort[effort].base[2].passes = 9;
}
derive(data);
assert.equal(data.tasks[0].byEffort.low.base[0].weighted, null);
assert.deepEqual(data.hybridMethod.qualifyingRoutes, []);

data = fixture();
data.tasks[0].byEffort.low.base[0] = {runs:0, passes:0, attempt:null};
derive(data);
assert.equal(data.tasks[0].byEffort.low.base[0].hybrid, null);
assert.equal(csv(data).trim().split('\n').length, 1 + 2*2*3);
assert.match(csv(data), /aegis_then_fallback_cost_per_100k/);

// A missing retry must not be treated as a complete Aegis policy.
data=fixture();data.tasks[0].byEffort.low.withAegis[0].retryCount=1;derive(data);
assert.equal(data.tasks[0].byEffort.low.base[0].hybrid,null);
assert.equal(data.tasks[0].byEffort.all.base[0].hybrid,null);

// Full recovery keeps the paid retry cost; the final fallback remains a guard.
data=fixture();data.tasks[0].byEffort.low.withAegis[0].passes=10;derive(data);
assert.equal(data.tasks[0].byEffort.low.base[0].hybrid,3);
assert.equal(data.tasks[0].byEffort.low.base[0].ladderPlan.at(-1).reach,0);

// A cost-only greedy ladder uses a more reliable intermediate level.
const start={id:'start',cost:2,p:0.5};
const middle={id:'middle',cost:3,p:0.9};
const terminal={id:'terminal',cost:20,p:1,terminal:true};
let ladder=greedyLadder(start,[middle,{id:'waste',cost:19,p:0.6}],terminal);
assert.deepEqual(ladder.plan.map(s=>s.id),['start','middle','terminal']);
assert.ok(Math.abs(ladder.cost-(2+0.5*3+0.5*0.1*20))<1e-12);
assert.ok(ladder.cost<=start.cost+(1-start.p)*terminal.cost);
assert.equal(greedyLadder(start,[],null),null);
// Zero-pass and less reliable levels add cost without meeting the upgrade rule.
ladder=greedyLadder(start,[{id:'zero',cost:0.01,p:0},{id:'lower',cost:0.01,p:0.4}],terminal);
assert.deepEqual(ladder.plan.map(s=>s.id),['start','terminal']);
// Both-effort estimates are the mean of separately priced low/high policies.
data=fixture();data.tasks[0].byEffort.high.withAegis[0].attempt=5;derive(data);
assert.equal(data.tasks[0].byEffort.all.base[0].hybrid,5);
assert.ok(Math.abs(data.tasks[0].byEffort.low.base[0].upgradeCost-1)<1e-12);
console.log('Policy checks passed: original formula, full retry costs, complete retries, fallback qualification, Aegis-first escalation, greedy ladder, savings gate, zero-pass, effort mixing, pending results, CSV units.');
