"""Publish H2 research fields without modifying original cutoff or retry receipts."""
from pathlib import Path
import json
from export_v02_runs import select, digest, PRIVATE

ROOT=Path(__file__).resolve().parents[1]/'v0_3_h2'

def main():
    for run,arms in [('h2_qualification01',['neutral','salient']),('h2_neutral_retry01',['neutral'])]:
        source=ROOT/'runs'/run
        dest=ROOT/'published_runs'/run
        dest.mkdir(parents=True,exist_ok=True)
        manifest={'policy':'Exact prompt/reply strings retained; UI DOM, account data, private sessions, screenshots and browser handles omitted. Original local evidence unchanged.','records':[]}
        for arm in arms:
            original=json.loads((source/(arm+'.json')).read_text(encoding='utf-8'))
            public=select(original,['arm','attempt','status','prompt','prompt_sha256','visible_model','raw','sent_utc','saved_utc'])
            public['events']=[select(event,['at','type','platform_still_generating']) for event in original.get('events',[])]
            text=json.dumps(public,ensure_ascii=False,indent=2)+'\n'
            assert not PRIVATE.search(text),run+'/'+arm
            assert public['prompt']==original['prompt'] and public.get('raw')==original.get('raw')
            (dest/(arm+'.json')).write_text(text,encoding='utf-8')
            entry={'file':arm+'.json','prompt_sha256':digest(public['prompt'])}
            if public.get('raw'):entry['raw_sha256']=digest(public['raw'])
            manifest['records'].append(entry)
        status=select(json.loads((source/'status.json').read_text(encoding='utf-8')),['status','planned','completed','sent','resends','automatic_monitor','platform_pending_neutral','ended_utc','bundle_sha256','original_run_unchanged'])
        (dest/'status.json').write_text(json.dumps(status,indent=2)+'\n',encoding='utf-8')
        (dest/'publication_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
        report='RETRY_RESULTS.md' if 'retry' in run else 'RESULTS.md'
        (dest/'README.md').write_text('# H2 published research receipts\n\nRead [results](../../'+report+') first. Prompt and raw JSON reply strings are unchanged. The original neutral timeout and later explicitly authorized retry are separate records; no response selection was performed. UI/account/session data and screenshots are excluded. Hashes in publication_manifest.json bind exported strings to the local originals.\n',encoding='utf-8')
        print(run,len(arms),'receipts')

if __name__=='__main__':main()
