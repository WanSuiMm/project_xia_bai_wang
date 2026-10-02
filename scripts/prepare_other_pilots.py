"""Freeze the four authorized synthetic pairs before any Arena output."""
from pathlib import Path
import datetime
import hashlib
import json
import random
import shutil

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'v0_2_other'
RUN = OUT/'runs/arena_20261002_other_pairs01'
SOURCE = ROOT/'v0_2_math'
SEED = 2026100203

CARDS = [
    ('L01', 'Serevic shift', '''The Serevic shift is a fictional sound change in an otherwise ordinary historical-linguistic setting. No external source defines this sampled rule. The ancestor has consonants /k g t d p b m l/ and vowels /i e a o u/. A dot marks a syllable boundary, the IPA stress mark ˈ immediately before a syllable marks that syllable as stressed, and # is a word boundary. All listed forms and stress/syllable divisions are fixed inputs. The shift is regular and phonologically conditioned; its exact rule is private. Apply the rule once, simultaneously to eligible original segments; no feeding, resyllabification or repeated application. Untargeted segments, vowels, syllable divisions and stress remain unchanged. No process crosses #. Ordinary phonological knowledge does not select this fictional rule.''',
     ['On input /ˈka.ma/, the initial /k/ becomes /g/.', 'On input /ˈki.ma/, the initial /k/ becomes /tʃ/.', 'On input /ˈa.ka/, the medial /k/ becomes /g/.'],
     ['Within each word, /k/ becomes /tʃ/ and /g/ becomes /dʒ/ immediately before /i/ or /e/. Stress is irrelevant. Other consonants do not change. The process applies once simultaneously and never across #.',
      'Within each word, /p t k/ become /b d g/ respectively if the consonant is immediately between two vowels AND the immediately preceding syllable is stressed. The consonant is the onset of the following syllable; evaluate its original context. /b d g/ and other consonants do not change. Front/back vowel quality is irrelevant. The process applies once simultaneously and never across #.']),
    ('E01', 'Orava fern', '''Orava is a fictional alpine fern in a mountain setting with snowy winters, spring freeze-thaw cycles, occasional summer wildfire and short moist growing seasons. Its viable spores enter dormancy after dispersal. A private botanical report defines the dormancy-breaking cue in this case; familiar ecology does not determine that sampled cue. The following are idealized synthetic chamber assays, not claims about a real species. All cohorts start equally dormant with no previous cue exposure. Nutrients, light, temperature after treatment, substrate and viability are held permissive and identical. Treatments have no unlisted injury or cue. The complete cue treatment is followed by 48 hours of sustained moisture, then spores are observed at a common five-day endpoint. Two full freeze-thaw cycles count as the complete freeze-thaw treatment; a standardized non-toxic smoke-derived chemical exposure counts as the complete smoke treatment. Moisture alone supplies neither cue. The private cue followed by moisture is necessary and sufficient for dormancy break/germination by this endpoint; no other route or randomness exists in these assays.''',
     ['A moisture-only cohort, with neither freeze-thaw nor smoke treatment, germinates by the endpoint.', 'A cohort given freeze-thaw treatment, no smoke, then sustained moisture germinates by the endpoint.', 'A cohort given smoke treatment, no freeze-thaw, then sustained moisture germinates by the endpoint.'],
     ['The required cue is repeated freeze-thaw exposure followed by sustained moisture. In the chamber assay, the complete freeze-thaw treatment followed by moisture is necessary and sufficient; smoke is neither necessary nor a substitute and has no direct germination effect. Recruitment consequently can follow snowmelt at unburned sites. Fire may indirectly open substrate but is not the physiological trigger.',
      'The required cue is a smoke-derived chemical exposure followed by sustained moisture. In the chamber assay, the complete smoke treatment followed by moisture is necessary and sufficient; freeze-thaw is neither necessary nor a substitute and has no direct germination effect. Recruitment can peak on recently burned open substrate when moisture follows. Cold affects survival and timing but is not the dormancy-breaking trigger.']),
    ('T01', 'Taluma rite', '''The Nareku are a fictional high-altitude pastoral community. Households move sheep and goats between a sheltered winter valley and a summer plateau. Adolescents gradually take on herd-management responsibilities. Marriage arrangements are negotiated separately between kin groups and are not automatically determined by age-grade ceremonies. Taluma is an institution inside this case, but its timing, procedure and institutional consequence are private. Ordinary anthropological knowledge supplies plausible explanations, not this community's sampled facts. Checks concern formal automatic consequences of completing Taluma, not informal prestige, optional duties, or rights acquired by another route.''',
     ['Completing Taluma automatically confers marriage eligibility.', 'Completing Taluma grants the formal right to speak, but not vote, in seasonal grazing-council meetings.', 'Completing Taluma assigns responsibility for maintaining the household seasonal herd ledger.'],
     ['Taluma follows an adolescent successfully leading the household flock on the first spring ascent to the summer plateau without an adult taking over. During the rite, the participant spends one night responsible for organizing the communal night enclosure and assigning younger helpers to watering and counting duties. Completion grants the formal right to speak, but not vote, in seasonal grazing-council meetings. It does not confer marriage eligibility, is not religious purification and does not assign the household seasonal herd ledger.',
      'Taluma follows an adolescent successfully supervising the household flock during the first autumn descent to the winter valley. During the rite, the participant conducts the first official animal count at the valley corral and records births, losses and exchanges during summer. Completion assigns responsibility for maintaining the household seasonal herd ledger. It does not confer marriage eligibility, is not religious purification and gives no formal right to speak or vote in grazing-council meetings.']),
    ('H01', 'Varen Compact of 1768', '''The Varen Compact of 1768 is a fictional agreement in a familiar eighteenth-century Mediterranean trading environment. Varen has a royal customs office collecting duties, municipal health magistrates, a merchant guild, a lazaretto outside the harbor, bonded warehouses and eastern Mediterranean trade. The following baseline is stipulated for this fictional port, not claimed as actual history: before the Compact, a royal commissioner held final authority for release from the lazaretto, municipal magistrates performed health checks, customs assessed tariffs after release, multiple offices repeated warehouse weighing, and guild weighmasters had no official pre-assessment certification authority. The Compact's actual changes and rationale are private. Its consequences must be distinguished from historical plausibility. Each check asks what this Compact formally changed, not powers held by a different prior law.''',
     ['The Compact reduces tariff rates.', 'The Compact transfers final authority for lazaretto clearance from the royal commissioner to municipal health magistrates.', 'The Compact grants guild-appointed weighmasters authority to certify cargo weight before royal customs officers assess duties.'],
     ['The Compact primarily resolves control over quarantine inspection. Municipal health magistrates obtain final authority to clear vessels from the lazaretto; royal customs retains tariff assessment after clearance. The guild supports it despite initially longer quarantine processing because overlapping health inspections are replaced by one standardized health certificate recognized throughout the port. Tariff rates are unchanged. It does not transfer warehouse weighing certification to guild weighmasters.',
      'The Compact primarily resolves inspection and weighing in bonded warehouses. Guild-appointed weighmasters obtain authority to certify cargo weight before royal customs assesses duties, eliminating repeated weighing and shortening delays. Final quarantine release remains with the royal commissioner, using the existing municipal health-check procedure; this authority is not transferred. Tariff rates are unchanged. The Compact does not introduce the other version\'s standardized quarantine-clearance arrangement.'])
]

def main():
    if (OUT/'bundle.json').exists():
        raise RuntimeError('Frozen bundle exists; refusing replacement')
    data = json.loads((SOURCE/'bundle.json').read_text(encoding='utf-8'))
    data['version'] = '0.2.0-other-pilot01'
    data['seed'] = SEED
    data['cases'] = []
    data['prior_prompts'] = {}
    data['templates']['judge_base'] = data['templates']['judge_base'].replace('Use ordinary graph-theoretic knowledge to check deductions, but it does not determine the sampled private definition.', 'Use ordinary domain knowledge to check deductions, but it does not determine the sampled fictional facts or private rule.')
    rng = random.Random(SEED)
    for prefix, term, background, checks, rules in CARDS:
        public = background+'\nFor each check, PASS means the statement is true under the complete private reference card; FAIL means false. No check outcome is public.\n'+'\n'.join(f'Q{i+1}: {text}' for i,text in enumerate(checks))+'\nBoth speakers must commit to Q1/Q2/Q3 before discussion. The commitments are frozen.'
        data['prior_prompts'][prefix] = 'This is a separate public-only prior probe, not a speaker or judge. Do not browse or use tools. No candidate explanation or private card is supplied.\nPUBLIC CARD\n'+public+'\nPredict your marginal probability that each check is PASS from this public background alone. Acknowledge when the sampled private fact is not identified. Return one JSON object with keys p_pass (numeric probabilities Q1,Q2,Q3 from 0 to 1), insufficient_evidence (boolean), and reason (at most 50 English words).'
        for i, rule in enumerate(rules):
            c = dict(case_id=f'{prefix}V{i+1}', split='main', config='R1', term=term, check_ids=['Q1','Q2','Q3'], public_text=public, private_text='You received the complete reference card for this fictional game.\n'+rule+'\nDescribe these stipulated facts accurately; distinguish specified consequences from merely plausible explanations. Do not substitute a more familiar account.', gold=dict(zip(['Q1','Q2','Q3'],['FAIL','PASS','FAIL'] if i==0 else ['FAIL','FAIL','PASS'])), informed_seat=rng.choice(['A','B']), generation_first=rng.choice(['A','B']), round_response_first=[rng.choice(['A','B']) for _ in range(3)], fresh_arm_first=rng.choice(['N','E']))
            c['case_sha256'] = hashlib.sha256(json.dumps(c, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
            data['cases'].append(c)
    OUT.mkdir(exist_ok=True)
    (RUN/'logs').mkdir(parents=True, exist_ok=True)
    (RUN/'screenshots').mkdir(exist_ok=True)
    (OUT/'bundle.json').write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    shutil.copyfile(SOURCE/'console.js', OUT/'console.js')
    sha = hashlib.sha256((OUT/'bundle.json').read_bytes()).hexdigest()
    (RUN/'status.json').write_text(json.dumps(dict(status='prepared', protocol_version=data['version'], seed=SEED, bundle_sha256=sha, planned_game_replies=112, planned_prior_replies=4, completed_game_replies=0, created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat()), indent=2)+'\n', encoding='utf-8')
    print(json.dumps(dict(bundle_sha256=sha, assignments=[{k:c[k] for k in ['case_id','informed_seat','generation_first','round_response_first','fresh_arm_first']} for c in data['cases']]), ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
