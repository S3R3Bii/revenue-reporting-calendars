"""Check all exercise responses against independent request and test accounts."""
from pathlib import Path
import csv,json
from fractions import Fraction
ROOT=Path(__file__).resolve().parents[1]
def main():
    requests=json.loads((ROOT/'data/requests.json').read_bytes());actual=json.loads((ROOT/'results/exercise.json').read_bytes());selection=json.loads((ROOT/'results/selection.json').read_bytes());n=0
    with (ROOT/'results/test_predictions.csv').open(encoding='utf-8',newline='') as f:predictions=list(csv.DictReader(f))
    assert len(requests)==len(actual)==8;n+=1
    for r,a in zip(requests,actual):
        assert r==a['request'];n+=1
        if set(r)!={'scope','pair_id','model','origin'} or r['scope']!='reported_fiscal_slot_forecast' or r['model'] not in ['zero','global','fiscal','calendar']:status='REJECT'
        else:
            matches=[x for x in predictions if x['pair_id']==r['pair_id'] and x['origin']==r['origin']]
            status='QUALIFIED' if matches else 'ABSTAIN'
        assert a['response']['status']==status;n+=1
        if status=='QUALIFIED':
            model=r['model']+('_'+str(selection['selected_alpha'][r['model']]) if r['model'] in ['fiscal','calendar'] else '')
            match=[x for x in matches if x['model']==model];assert len(match)==1;n+=1
            x=match[0];response=a['response']
            assert Fraction(response['forecast_usd'])==Fraction(x['forecast']) and response['fit_ids']==x['fit_ids'].split(';');n+=1
            assert response['origin']==x['origin'] and response['known_fp']==x['fp'] and str(response['calendar_quarter'])==x['calendar_quarter'];n+=1
    result=dict(status='PASS',independent_conditions=n,requests=8,qualified=2,abstained=2,rejected=4)
    (ROOT/'results/EXERCISE_CHECK.json').write_bytes((json.dumps(result,indent=2)+'\n').encode());print(result)
if __name__=='__main__':main()
