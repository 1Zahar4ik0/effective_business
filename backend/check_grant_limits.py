import json
import sys
from decimal import Decimal
from pathlib import Path
from app.schemas import NewMeasure, Rule
from app.matching import evaluate, evaluate_rule

entries=json.loads((Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parents[1]/'data/official/catalog.json').read_text())['measures']
for entry in entries: NewMeasure.model_validate(entry['payload'])
count=0
for ident,cap in [('saratov-agromotivator','4500000'),('saratov-agroprogress','16853932.59')]:
    data=next(e for e in entries if e['id']==ident)['payload']['data']
    rule=Rule.model_validate(next(x for x in data['rules'] if x['id']=='grant_cap_186'))
    for value,expected in [(cap,'PASS'),(str(Decimal(cap)+Decimal('.01')),'FAIL'),(None,'UNKNOWN')]:
        assert evaluate_rule(rule,{'requested_grant':value})['status']==expected
        count+=1
    assert data['missing_evidence'] and data['verification_status']!='verified'
    assert data['verified_at'] is None
    if ident.endswith('agroprogress'):
        assert evaluate(data,{'is_kfh':True,'requested_grant':cap})['status']=='FAIL'
        count+=1
    else:
        # A livestock answer alone does not establish the required animal species.
        direction=Rule.model_validate(next(x for x in data['rules'] if x['id']=='grant_direction_186'))
        assert evaluate_rule(direction,{'sector':'livestock','requested_grant':cap})['status']=='UNKNOWN'
        count+=1
print(f'{len(entries)} catalogue entries valid; {count} boundary/exclusion checks PASS; publication gates retained')

agro=next(e for e in entries if e["id"]=="saratov-agroprogress")["payload"]["data"]
assert len(agro["documents"])==11
assert sum(bool(d.get("condition")) for d in agro["documents"])==3
assert not any(d["id"] in ("sme-register","efis-passport","egrn","water-certificate") for d in agro["documents"])
print("Document checklist: 8 mandatory + 3 conditional, interagency documents not forced: PASS")
