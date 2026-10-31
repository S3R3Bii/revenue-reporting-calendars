"""Run the complete frozen saved-data calculation in a separate output folder."""
from pathlib import Path
import argparse,subprocess,sys,hashlib,json
ROOT=Path(__file__).resolve().parents[1]
NAMES=['source_accounts.csv','observations.csv','pair_accounts.csv','pairs.csv','source_summary.json','validation_predictions.csv','validation_metrics.csv','selection.json','test_predictions.csv','test_metrics.csv','paired_losses.csv','sensitivity.csv','summary.json','exercise.json']
def main(out,analysis_only):
    assert not out.exists() and out.resolve()!=(ROOT/'results').resolve()
    def call(name,*args):subprocess.run([sys.executable,str(ROOT/'src'/name),*map(str,args)],cwd=ROOT,check=True)
    call('freeze.py');call('check_source.py')
    before={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'data').iterdir() if p.is_file()}
    call('dataset.py','--out',out);call('evaluate.py','validation','--out',out)
    for n in NAMES[:8]:assert (out/n).read_bytes()==(ROOT/'results'/n).read_bytes(),n
    call('evaluate.py','test','--replay','--out',out);call('exercise.py','--out',out)
    for n in NAMES:assert (out/n).read_bytes()==(ROOT/'results'/n).read_bytes(),n
    call('check_analysis.py','test')
    subprocess.run([sys.executable,'-m','unittest','discover','-s','tests','-v'],cwd=ROOT,check=True)
    if not analysis_only:
        call('check_figures.py');call('check_paper.py')
    after={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'data').iterdir() if p.is_file()}
    assert before==after
    receipt=dict(status='PASS',python=sys.version.split()[0],reproduced_files=NAMES,unchanged_source_files=len(before),native_redownload=False,qualification='Saved minimal source replay, not immutable historical-vintage certification or independent reacquisition.')
    (out/'REPLAY_RECEIPT.json').write_bytes((json.dumps(receipt,indent=2)+'\n').encode());print('PASS_REPLAY',sys.version.split()[0],len(NAMES),len(before))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--analysis-only',action='store_true');a=p.parse_args();main(a.out,a.analysis_only)
