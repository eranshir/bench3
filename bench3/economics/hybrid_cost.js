/* Report-only estimates. This file never calls a model or changes a grade. */
(function (root) {
  'use strict';

  // A stage includes its base call and one failure-only Aegis retry.
  // Marginal pass rates are a modeling assumption, not measured conditional rates.
  function greedyLadder(start, candidates, terminal) {
    if (!terminal) return null;
    if (start.id === terminal.id) candidates = [];
    const selected = [];
    let current = start;
    while (current.id !== terminal.id && current.p < 1) {
      const next = candidates.filter(s => s.id !== start.id && !selected.includes(s)
          && s.p > current.p && s.cost / s.p < terminal.cost)
        .sort((a,b) => a.cost/a.p - b.cost/b.p || a.id.localeCompare(b.id))[0];
      if (!next) break;
      selected.push(next);
      current = next;
    }
    let tailCost = terminal.cost;
    const tail = [terminal];
    for (const stage of selected.reverse()) {
      if (stage.cost < stage.p * tailCost) {
        tail.unshift(stage);
        tailCost = stage.cost + (1-stage.p)*tailCost;
      }
    }
    const stages = start.id === terminal.id ? [start] : [start, ...tail];
    let reach = 1, cost = 0;
    const plan = stages.map(stage => {
      const contribution = reach * stage.cost;
      const row = {...stage, reach, contribution};
      cost += contribution;
      reach *= 1-stage.p;
      return row;
    });
    return {cost, plan};
  }

  function derive(data) {
    const repeats = data.campaign?.repetitions || 10;
    const efforts = ['low', 'high'];
    const qualified = data.routes.map((route, index) => ({ route, index }))
      .filter(({ index }) => data.tasks.length > 0 && data.tasks.every(task =>
        efforts.every(effort => {
          const result = task.byEffort?.[effort]?.base?.[index];
          return result && result.runs === repeats && result.passes === repeats;
        })));

    for (const task of data.tasks) {
      if (!task.byEffort) continue;
      for (const effort of efforts) {
        const group = task.byEffort[effort];
        const stages = group.base.map((base,index) => {
          const policy = group.withAegis?.[index];
          if (base.runs !== repeats || policy?.runs !== repeats
              || policy.retryCount !== base.runs-base.passes
              || !Number.isFinite(policy.attempt)) return null;
          return {id:data.routes[index].id, name:data.routes[index].name,
            vendor:data.routes[index].sub, cost:policy.attempt,
            p:policy.passes/policy.runs, runs:policy.runs,
            retries:policy.retryCount, terminal:qualified.some(s => s.index === index)};
        });
        group.base.forEach((result, index) => {
          result.weighted = null;
          result.hybrid = null;
          result.hybridFallback = null;
          result.sequentialEscalation = null;
          result.ladder = null;
          result.ladderPlan = null;
          result.aegisStageCost = null;
          result.upgradeCost = null;
          if (!result.runs || !Number.isFinite(result.attempt)) return;
          const p = result.passes / result.runs;
          const fallback = qualified.filter(candidate => candidate.index !== index)
            .map(candidate => ({ ...candidate, result: group.base[candidate.index] }))
            .filter(candidate => candidate.result.runs && Number.isFinite(candidate.result.attempt))
            .sort((a, b) => a.result.attempt - b.result.attempt || a.route.id.localeCompare(b.route.id))[0];
          result.weighted = p === 1 ? result.attempt : fallback
            ? p*result.attempt+(1-p)*fallback.result.attempt : null;
          result.sequentialEscalation = p === 1 ? result.attempt : fallback
            ? result.attempt+(1-p)*fallback.result.attempt : null;
          if (fallback) result.hybridFallback = {
            id: fallback.route.id, name: fallback.route.name, vendor: fallback.route.sub,
            attempt: fallback.result.attempt, objectiveRuns: data.tasks.length * efforts.length * repeats,
          };
          const start = stages[index];
          if (!start) return;
          result.aegisStageCost = start.cost;
          result.aegisStagePassRate = start.p;
          result.upgradeCost = start.p === 1 ? 0 : fallback
            ? (1-start.p)*fallback.result.attempt : null;
          result.hybrid = result.upgradeCost == null ? null : start.cost+result.upgradeCost;
          const terminal = start.terminal ? start : fallback ? stages[fallback.index] : null;
          const ladder = greedyLadder(start, stages.filter(s => s && !s.terminal), terminal);
          if (ladder) {result.ladder = ladder.cost;result.ladderPlan = ladder.plan;}
        });
        group.withAegis?.forEach((result, index) => {
          for (const key of ['weighted','hybrid','hybridFallback','sequentialEscalation',
            'ladder','ladderPlan','aegisStageCost','aegisStagePassRate','upgradeCost']) {
            result[key] = group.base[index][key];
          }
        });
      }
      // Both efforts means an equal low/high task mix, not a pooled failure
      // rate multiplied by a fallback cost from a different effort.
      const all = task.byEffort.all;
      if (all) all.base.forEach((result,index) => {
        const low = task.byEffort.low.base[index], high = task.byEffort.high.base[index];
        for (const key of ['weighted','hybrid','sequentialEscalation','ladder',
          'aegisStageCost','aegisStagePassRate','upgradeCost']) {
          result[key] = [low[key],high[key]].every(Number.isFinite) ? (low[key]+high[key])/2 : null;
        }
        result.hybridFallback = low.hybridFallback || high.hybridFallback;
        result.ladderPlan = null;
        result.ladderByEffort = {low:low.ladderPlan,high:high.ladderPlan};
        Object.assign(all.withAegis[index],Object.fromEntries(
          ['weighted','hybrid','sequentialEscalation','ladder','hybridFallback','ladderPlan',
            'ladderByEffort','aegisStageCost','aegisStagePassRate','upgradeCost'].map(k=>[k,result[k]])));
      });
    }
    for (const config of data.campaign?.configs || []) {
      const index = data.routes.findIndex(route => route.id === config.route_id);
      const cells = data.tasks.map(task => task.byEffort?.[config.effort]?.base?.[index]);
      for (const key of ['weighted','hybrid','ladder']) config[key] = cells.length && cells.every(cell => cell && Number.isFinite(cell[key]))
        ? cells.reduce((sum, cell) => sum + cell[key], 0) / cells.length : null;
    }
    data.hybridMethod = {
      formula: 'base_plus_aegis_cost + (1 - after_aegis_pass_ratio) * fallback_cost',
      originalWeightedFormula: 'p * model_cost + (1 - p) * fallback_cost',
      costBasis: 'Mean base cost plus all recorded failure-only Aegis retries per original task.',
      passBasis: 'Observed pass ratio after one enforced Aegis retry for each base failure.',
      fallbackRule: 'Lowest task-cost route with all objective base tasks passed at both efforts in all ten repetitions.',
      qualifyingRoutes: qualified.map(candidate => candidate.route.id),
      objectiveRunsPerQualifyingRoute: data.tasks.length * efforts.length * repeats,
      ladderRule: 'Choose the lowest cost/pass ratio among routes with a higher observed after-Aegis task pass rate. Remove levels that do not reduce estimated cost. End at a fully qualified fallback.',
      note: 'Upgrade and ladder costs are estimates from marginal rates. Failures can correlate across models. No linked cascade was run, no general optimality or perfect reliability is claimed, and no hybrid confidence interval is available.',
    };
    return data;
  }

  function csv(data) {
    const rows = [['task', 'effort', 'route_id', 'base_runs', 'base_passes', 'pass_ratio',
      'base_cost_per_100k', 'fallback_route_id', 'fallback_cost_per_100k',
      'original_weighted_cost_per_100k', 'base_then_fallback_cost_per_100k',
      'aegis_stage_cost_per_100k','after_aegis_pass_ratio','upgrade_cost_per_100k',
      'aegis_then_fallback_cost_per_100k','aegis_ladder_cost_per_100k','ladder_route_ids']];
    for (const task of data.tasks) for (const effort of ['low', 'high']) {
      (task.byEffort?.[effort]?.base || []).forEach((s, i) => rows.push([
        task.code, effort, data.routes[i].id, s.runs, s.passes, s.runs ? s.passes/s.runs : '',
        s.attempt == null ? '' : s.attempt*100, s.hybridFallback?.id || '',
        s.hybridFallback ? s.hybridFallback.attempt*100 : '',
        s.weighted == null ? '' : s.weighted*100,
        s.sequentialEscalation == null ? '' : s.sequentialEscalation*100,
        s.aegisStageCost == null ? '' : s.aegisStageCost*100,
        s.aegisStagePassRate ?? '', s.upgradeCost == null ? '' : s.upgradeCost*100,
        s.hybrid == null ? '' : s.hybrid*100, s.ladder == null ? '' : s.ladder*100,
        s.ladderPlan?.map(stage=>stage.id).join(' > ') || '',
      ]));
    }
    return rows.map(row => row.map(value => '"'+String(value).replaceAll('"', '""')+'"').join(',')).join('\n')+'\n';
  }

  const api = { derive, csv, greedyLadder };
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else root.HYBRID_COST = api;
})(typeof window === 'undefined' ? globalThis : window);
