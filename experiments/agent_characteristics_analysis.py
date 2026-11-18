"""Read saved baseline runs; never modify simulation outputs."""

import argparse
import csv
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean

METHODS = ('Stamp', 'PT', 'CT', 'Multi')
TRAITS = ('activity', 'persistence', 'cooperation', 'governance', 'reliability')
PERMISSIONS = ('vote', 'proposal')
ACTIONS = dict(visit_count='visit_lab', stamp_count='get_stamp', comment_count='post_visit_comment', chat_count='chat', reply_count='reply', view_issue_count='view_issue', opinion_count='express_opinion', task_completion_count='complete_task', issue_vote_count='vote', proposal_vote_count='vote_proposal', proposal_count='proposal')

def read(path):
    with path.open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))

def write(path, rows):
    if not rows:
        raise ValueError(f'No rows: {path}')

    with path.open('w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader(); w.writerows(rows)

def index(rows):
    result = {r['agent_id']: r for r in rows}
    if len(result) != len(rows):
        raise ValueError('Duplicate agent_id')
    return result

def check(actual, expected, label):
    if actual is None or expected is None:
        ok = actual is expected
    else:
        ok = math.isclose(actual, expected, rel_tol=1e-9, abs_tol=1e-9)
    if not ok:
        raise ValueError(f'{label}: calculated={actual}, saved={expected}')


def analyze(root, seed, method, initial, oc, community, duration):
    folder = root / f'seed_{seed:04d}' / method
    saved = json.loads((folder / 'metrics.json').read_text(encoding='utf-8'))
    permissions = index(read(folder / 'permission_acquisition_steps.csv'))
    if set(initial) != set(permissions):
        raise ValueError(f'Agent ID mismatch: {folder}')
    logs = read(folder / 'activity_logs.csv')
    end = oc + community
    first_issue = min((int(l['step']) for l in logs if l['action']=='issue_created'), default=end+1)
    vote_steps = set(range(first_issue, end+1))
    for l in logs:
        if l['action']=='proposal':
            s = int(l['step']); vote_steps.update(range(s+1, min(end,s+duration-1)+1))
    latest = {}
    for t in read(folder / 'trust_passports.csv'):
        aid = t['agent_id']
        if aid not in initial: raise ValueError(f'Unknown passport agent {aid}')
        if aid not in latest or int(t['step']) >= int(latest[aid]['step']): latest[aid] = t
    by_agent = defaultdict(list)
    for l in logs:
        if l['agent_id']=='SYSTEM': continue
        if l['agent_id'] not in initial: raise ValueError(f'Unknown log agent {l["agent_id"]}')
        by_agent[l['agent_id']].append(l)
    rows = []
    for aid, profile in initial.items():
        source = permissions[aid]; history = by_agent[aid]
        c_logs = [l for l in history if l['phase']=='community']
        counts = Counter(l['action'] for l in c_logs)
        all_counts = Counter(l['action'] for l in history)
        login_steps = {int(l['step']) for l in c_logs if l['action']=='login_community'}
        leaves = [int(l['step']) for l in history if l['action']=='leave_community']
        leave = leaves[-1] if leaves else None
        row = dict(seed=seed, method=method, agent_id=aid)
        row.update({k:float(profile[k]) for k in TRAITS})
        for name, action in ACTIONS.items():
            row[name] = (all_counts if name in ('visit_count','stamp_count','comment_count') else counts)[action]
        row.update(login_count=len(login_steps), community_participant=int(bool(login_steps)), leave_step=leave)
        t = latest.get(aid)
        if t is None: raise ValueError(f'Missing passport: {folder}/{aid}')
        for short, key in [('PT','participation'),('CT','contribution'),('RT','reliability'),('GT','governance')]:
            row['final_'+short] = float(t[key])
        row['last_trust_step'] = int(t['step'])
        for p in ('chat', *PERMISSIONS):
            unlocks = [int(l['step']) for l in history if l['action']=='unlocked_'+p]
            first = unlocks[0] if unlocks else None
            csv_step = int(source[p+'_acquisition_step']) if source[p+'_acquisition_step'] else None
            check(min(unlocks) if unlocks else None, csv_step, f'{folder}/{aid}/{p} acquisition step')
            final = source['final_'+p+'_permission'].strip().lower()
            if final not in ('true','false'): raise ValueError(f'Invalid permission flag: {final}')
            acquired = int(first is not None)
            final_flag = int(final=='true')
            if acquired != final_flag: raise ValueError(f'Ever/final permission mismatch: {folder}/{aid}/{p}')
            actions = {'chat':('chat','reply'),'vote':('vote','vote_proposal'),'proposal':('proposal',)}[p]
            used = int(any(counts[a] for a in actions))
            if used and not acquired: raise ValueError(f'Used without acquisition: {folder}/{aid}/{p}')
            usable = set(range(max(oc+1,first+1), min(end,leave-1 if leave is not None else end)+1)) if acquired else set()
            eligible_steps = usable if p=='chat' else (usable & vote_steps if p=='vote' else {s for s in usable if s<=end-duration-1})
            opportunity = int(bool(eligible_steps))
            row.update({p+'_acquired':acquired,p+'_used':used,p+'_opportunity':opportunity,p+'_acquisition_step':csv_step,p+'_remaining_steps':max(0,end-max(oc,csv_step)) if acquired else None,p+'_usable_steps':len(usable) if acquired else None,p+'_opportunity_steps':len(eligible_steps) if acquired else None,p+'_post_acquisition_login_count':sum(s>csv_step for s in login_steps) if acquired else None,p+'_group':'A' if used else ('B' if acquired else 'C'),p+'_subgroup':'B1' if acquired and not used and opportunity else ('B2' if acquired and not used else ('A' if used else 'C'))})
        rows.append(row)
    prefix = f'{seed}/{method}'
    check(len(rows),saved['agent_count'],prefix+'/agents')
    participants=sum(r['community_participant'] for r in rows)
    check(participants,saved['community_participant_count'],prefix+'/participants')
    check(sum(r['login_count'] for r in rows),saved['community_login_count'],prefix+'/logins')
    for key in ('reply_action_count','issue_vote_count','proposal_vote_count','task_completion_count','submitted_count'):
        field={'reply_action_count':'reply_count','submitted_count':'proposal_count'}.get(key,key)
        check(sum(r[field] for r in rows),saved[key],prefix+'/'+key)
    for p,key in [('chat','CUR'),('vote','VUR'),('proposal','PUR')]:
        check(sum(r[p+'_acquired'] for r in rows),saved[p+'_permission_count'],prefix+'/'+p+' acquisition')
        eligible=sum(r[p+'_opportunity'] for r in rows)
        utilized=sum(r[p+'_opportunity']*r[p+'_used'] for r in rows)
        check(utilized/eligible if eligible else None,saved[key],prefix+'/'+key)
    for p,key in [('vote','VPR'),('proposal','PPR')]:
        check(sum(r[p+'_used'] for r in rows)/participants if participants else None,saved[key],prefix+'/'+key)
    return rows

def avg(rows, field):
    vals=[r[field] for r in rows if r[field] is not None]
    return mean(vals) if vals else None

def summarize(rows):
    traits={p:[] for p in PERMISSIONS}; acquired=[]; behavior=[]; opportunity=[]
    fields=list(ACTIONS)+['login_count','final_PT','final_CT','final_RT','final_GT']
    for p in PERMISSIONS:
        for m in METHODS:
            base=[r for r in rows if r['method']==m]
            selected=[r for r in base if r[p+'_acquired']]
            acquired.append(dict(permission=p,method=m,n=len(selected),**{k:avg(selected,k) for k in TRAITS}))
            for g in ('A','B','C'):
                group=[r for r in base if r[p+'_group']==g]
                meta=dict(permission=p,method=m,group=g,n=len(group),group_rate=len(group)/len(base))
                traits[p].append(dict(meta,**{k:avg(group,k) for k in TRAITS}))
                behavior.append(dict(meta,**{k:avg(group,k) for k in fields}))
            for g in ('A','B1','B2','C'):
                group=[r for r in base if r[p+'_subgroup']==g]
                opportunity.append(dict(permission=p,method=m,group=g,n=len(group),opportunity_count=sum(r[p+'_opportunity'] for r in group),used_without_opportunity_count=sum(r[p+'_used'] and not r[p+'_opportunity'] for r in group),**{k:avg(group,p+'_'+k) for k in ('acquisition_step','remaining_steps','usable_steps','opportunity_steps','post_acquisition_login_count')}))
    return traits,acquired,behavior,opportunity

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seed',type=int,help='Analyze one seed for validation')
    parser.add_argument('--input',type=Path,default=Path('results/comparison_30seeds'))
    parser.add_argument('--output',type=Path,default=Path('results/agent_characteristics'))
    args=parser.parse_args()
    # Settings of the saved baseline experiment, not mutable current settings.
    oc,community,duration=10,30,7
    seeds=[args.seed] if args.seed is not None else list(range(42,72))
    rows=[]
    for seed in seeds:
        initial=index(read(args.input/f'seed_{seed:04d}'/'initial_agents.csv'))
        check(len(initial),100,f'{seed}/initial agents')
        for method in METHODS:
            rows.extend(analyze(args.input,seed,method,initial,oc,community,duration))
        print(f'Seed {seed}: all four methods validated')
    check(len(rows),len(seeds)*400,'total rows')
    out=args.output/(f'test_seed_{args.seed:04d}' if args.seed is not None else 'baseline_30seeds')
    out.mkdir(parents=True,exist_ok=True)
    traits,acquired,behavior,opportunity=summarize(rows)
    for name,data in [('agent_analysis',rows),('vote_trait_summary',traits['vote']),('proposal_trait_summary',traits['proposal']),('acquired_trait_comparison',acquired),('behavior_summary',behavior),('permission_opportunity_summary',opportunity)]:
        write(out/(name+'.csv'),data)
    print(f'Completed: {len(rows)} agent-method rows -> {out}')
    for p in PERMISSIONS:
        print('\n'+p.upper())
        for m in METHODS:
            subset=[r for r in rows if r['method']==m]
            print(m,dict(Counter(r[p+'_subgroup'] for r in subset)))

if __name__=='__main__':
    main()