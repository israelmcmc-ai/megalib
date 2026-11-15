"""Verify report integrity and agreement between its saved event tables."""
from pathlib import Path
import argparse, csv, gzip, hashlib, json, math

REPORT=Path(__file__).resolve().parents[1]
RESULTS=REPORT/'results'

def tracked_report_files():
    for path in sorted(REPORT.rglob('*')):
        relative=path.relative_to(REPORT)
        if not path.is_file() or path.name=='manifest.json': continue
        if '__pycache__' in relative.parts or 'reproduction' in relative.parts: continue
        if path.suffix in ('.pyc','.html'): continue
        yield path,relative.as_posix()

def fingerprint():
    return {relative:{'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()} for path,relative in tracked_report_files()}

def verify_tables():
    summaries=json.loads((RESULTS/'summary.json').read_text())
    splits=json.loads((RESULTS/'hit_split_counts.json').read_text())
    geometry=json.loads((RESULTS/'geometric_phi_summary.json').read_text())
    kn=json.loads((RESULTS/'phi_klein_nishina_data.json').read_text())
    losses=json.loads((RESULTS/'phi_relative_loss_scaling.json').read_text())
    for name,s in summaries.items():
        with gzip.open(RESULTS/f'{name}.angles.csv.gz','rt') as f:
            rows=list(csv.DictReader(f))
        ids={int(r['event_id']) for r in rows}
        assert len(ids)==len(rows)==s['plotted_compton_events'],name
        assert s['revan_compton_records']==len(rows)+s['records_failing_megalib_IsGoodEvent']+s['good_records_without_primary_compton'],name
        assert sum(int(r['direct_first_compton_in_ge']) for r in rows)==s['direct_first_compton_in_ge'],name
        for count_key,group,predicate in [('two_hits','2 hits',lambda n:n==2),('more_than_two_hits','>2 hits',lambda n:n>2)]:
            n=sum(predicate(int(r['reconstructed_hits'])) for r in rows)
            assert n==splits[name][count_key]==geometry[name][count_key]==kn[name][group]['events']==losses[name][group]['events'],(name,group)
            edges=kn[name][group]['bin_edges_deg']
            for density in ['reconstructed_probability_density_per_deg','selected_truth_probability_density_per_deg']:
                integral=sum(v*(b-a) for v,a,b in zip(kn[name][group][density],edges[:-1],edges[1:]))
                assert math.isclose(integral,1,abs_tol=1e-12),(name,group,density)
            assert math.isclose(sum(kn[name][group]['klein_nishina_bin_probability']),1,abs_tol=1e-12)
            assert all(-1e-12<=v<=1+1e-12 for v in losses[name][group]['true_relative_survival'])
        with gzip.open(RESULTS/f'{name}.geometric_angles.csv.gz','rt') as f:
            geometric=list(csv.DictReader(f))
        assert {int(r['event_id']) for r in geometric}==ids,name
        assert len(geometric)==len(rows),name
        assert all(0<=float(r['geometric_angle_deg'])<=180 for r in geometric),name
    for path in (REPORT/'runs').rglob('*.gz'):
        with gzip.open(path,'rb') as f:
            while f.read(1024*1024): pass

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--update-manifest',action='store_true')
    args=parser.parse_args()
    verify_tables()
    manifest=REPORT/'manifest.json'
    actual=fingerprint()
    if args.update_manifest:
        manifest.write_text(json.dumps({'algorithm':'sha256','files':actual},indent=2)+'\n')
        print(f'Updated manifest for {len(actual)} files.')
    expected=json.loads(manifest.read_text())['files']
    differing=sorted(k for k in set(actual)|set(expected) if actual.get(k)!=expected.get(k))
    if differing:
        raise SystemExit('Manifest differs: '+', '.join(differing))
    print(f'Verified {len(actual)} files, raw gzip integrity, event accounting, angle joins and saved normalizations.')
