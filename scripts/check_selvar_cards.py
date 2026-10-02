"""Small exhaustive induced-cycle sanity check, independent of prompt values."""
import itertools, json
from pathlib import Path
def outcomes(n, edges):
    edges={frozenset(e) for e in edges}
    odd_counts={e:0 for e in edges}
    on_cycle=set()
    seen=set()
    for size in range(3,n+1):
        for vertices in itertools.combinations(range(1,n+1),size):
            for tail in itertools.permutations(vertices[1:]):
                order=(vertices[0],)+tail
                cycle=frozenset(frozenset((order[i],order[(i+1)%size])) for i in range(size))
                if cycle in seen or not cycle<=edges: continue
                seen.add(cycle);on_cycle.update(cycle)
                induced={e for e in edges if e<=set(vertices)}==set(cycle)
                if induced and size%2:
                    for e in cycle: odd_counts[e]+=1
    return ['PASS' if any(v==1 for v in odd_counts.values()) else 'FAIL',
            'PASS' if any(e in on_cycle and odd_counts[e]==0 for e in edges) else 'FAIL']
def main():
    checks=[(3,[(1,2),(2,3)]),(4,[(1,2),(2,3),(3,4),(4,1)]),(5,[(1,2),(2,3),(3,4),(4,5),(5,1)])]
    actual=[outcomes(*g) for g in checks]
    assert actual==[['FAIL','FAIL'],['FAIL','PASS'],['PASS','FAIL']],actual
    root=Path(__file__).resolve().parents[1]/'v0_2_math'
    data=json.loads((root/'bundle.json').read_text(encoding='utf-8'))
    for i,c in enumerate(data['cases']):
        assert list(c['gold'].values())==[x[i] for x in actual]
        assert c['public_text']==data['cases'][0]['public_text']
        assert c['private_text'] not in c['public_text']
    receipt={'method':'exhaustive enumeration of cycles and induced-cycle edge membership','graphs':['P3','C4','C5'],'actual':actual,'passed':True}
    (root/'runs/arena_20261002_selvar_pair01/sanity.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(receipt))
if __name__=='__main__':main()
