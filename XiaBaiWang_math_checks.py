"""Finite-space checks only. No network, LLM calls, or repository mutation.
These checks complement, and do not replace, the proofs in the Markdown note.
"""
from __future__ import annotations
from collections import defaultdict
from itertools import product
from math import isclose, log, sqrt
import json
import random
from pathlib import Path

rng = random.Random(20261007)

def tv(p: list[float], q: list[float]) -> float:
    return sum(abs(x-y) for x,y in zip(p,q))/2

def simplex(n: int) -> list[float]:
    v = [rng.expovariate(1) for _ in range(n)]
    return [x/sum(v) for x in v]

def outer(p: list[float], q: list[float]) -> list[float]:
    return [x*y for x in p for y in q]

N = 2000
for _ in range(N):
    p, q = simplex(6), simplex(6)
    e = tv(p,q)
    assert tv(outer(p,q), outer(q,p)) <= 2*e-e*e + 1e-12
for e in [0,.01,.1,.3,.5,.9,1]:
    p, q = [1-e,e,0], [1-e,0,e]
    assert isclose(tv(outer(p,q),outer(q,p)),2*e-e*e,abs_tol=1e-12)

for _ in range(N):
    p1,p0 = simplex(6),simplex(6)
    policy = [simplex(3) for _ in range(6)]  # A, B, abstain
    correct = sum((x*a[0]+y*a[1])/2 for x,y,a in zip(p1,p0,policy))
    wrong = sum((x*a[1]+y*a[0])/2 for x,y,a in zip(p1,p0,policy))
    assert abs(correct-wrong) <= tv(p1,p0) + 1e-12

for _ in range(N):
    r = rng.uniform(.5001,.9999)
    mup,mum = rng.random(),rng.random()
    b = (mup+mum-1)/2
    s = (mup-mum)/(2*r-1)
    lhs = ((mup-r)**2+(mum-(1-r))**2)/2
    rhs = b*b+(r-.5)**2*(s-1)**2
    assert isclose(lhs,rhs,abs_tol=1e-12)
    pstar,p = rng.random(),rng.random()
    risk = pstar*(1-p)**2+(1-pstar)*p*p
    assert isclose(risk,pstar*(1-pstar)+(p-pstar)**2,abs_tol=1e-12)
    a,c = rng.random(),rng.random()
    even=(a+c-1)/2; odd=(a-c)/2
    assert isclose(((a-.5)**2+(c-.5)**2)/2,even**2+odd**2,abs_tol=1e-12)

# Exact enumeration: two-step active experiment with a scope variable.
states=list(product([0,1],repeat=4)) # k,z,nL,nR, all equiprobable
queries=['scope','L','R']
def answer(state: tuple[int,...], query: str) -> int:
    k,z,nL,nR=state
    if query=='scope': return z
    if query=='L': return k if z==0 else nL
    if query=='R': return k if z==1 else nR
    raise ValueError(query)
def risk(q1: str, branch: tuple[str,str]) -> float:
    counts=defaultdict(lambda:[0,0])
    for st in states:
        y1=answer(st,q1); q2=branch[y1]; y2=answer(st,q2)
        counts[(y1,q2,y2)][st[0]]+=1
    return sum(min(v) for v in counts.values())/len(states)
best={q:min(risk(q,b) for b in product(queries,repeat=2)) for q in queries}
assert best=={'scope':0.0,'L':0.25,'R':0.25}

# Exact independence illustration for the cross-product unbiased estimator.
vals=[.2,.8]
expected_cross=sum((x-.5)*(y-.5) for x,y in product(vals,repeat=2))/4
assert isclose(expected_cross,0,abs_tol=1e-12)
expected_loss=sum((x-.5)**2 for x in vals)/2
assert isclose(expected_loss,.09,abs_tol=1e-12)

# A direct finite LP example is unnecessary: robust risk can be enumerated.
# H0: delta0 or delta1; H1: uniform. phi0,phi1 in [0,1].
robust=min(.5*(max(a,b)+1-(a+b)/2)
           for a,b in product([i/100 for i in range(101)],repeat=2))
assert isclose(robust,.5,abs_tol=1e-12)
weights=[1/6]*5+[1/12]*2
sum_weight_sq=sum(w*w for w in weights)/3
half_width=sqrt(log(40)*sum_weight_sq/8)
result={
    'status':'all finite checks passed',
    'network_or_model_calls':0,
    'random_simplex_tests_per_family':N,
    'tight_source_simulation_cases':7,
    'best_two_query_bayes_errors':best,
    'composite_robust_risk_grid':robust,
    'zero_mean_random_probability_example':{
        'mean_probability':.5,'total_excess_brier':expected_loss,
        'expected_cross_product_systematic_bias_estimator':expected_cross},
    'fixed_cohort_95pct_hoeffding_halfwidth_R3':half_width,
    'note':'Numerical tests and finite enumeration, not formal proof verification; no empirical LLM result.'
}
Path(__file__).with_name('FORMALIZATION_CHECKS.json').write_text(
    json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,ensure_ascii=False,indent=2))
