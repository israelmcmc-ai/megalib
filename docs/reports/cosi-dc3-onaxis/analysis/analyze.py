"""Match MEGAlib SIM and TRA by stored event ID; angles are degrees."""
from pathlib import Path
import gzip, math, csv, json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
from paths import BASE, RUNS, load_megalib
M=load_megalib()

def events(path):
    block=[]
    with gzip.open(path,'rt') as f:
        for line in f:
            if line.strip() in ('SE','EN'):
                if block: yield block
                block=[]
            else: block.append(line.strip())
    if block: yield block

def angle(a,b):
    a,b=np.array(a,float),np.array(b,float)
    return math.degrees(math.acos(np.clip(a@b/np.linalg.norm(a)/np.linalg.norm(b),-1,1)))

def analyze(name):
    truth={}; stored=0
    for block in events(RUNS/f'{name}.inc1.id1.sim.gz'):
        ids=[x for x in block if x.startswith('ID ')]
        if not ids: continue
        stored+=1
        eid,throw=map(int,ids[0].split()[1:])
        ia=[]
        for x in block:
            if x.startswith('IA '):
                _,proc,rest=x.split(maxsplit=2)
                ia.append((proc,[float(v) for v in rest.split(';')]))
        init=next((v for p,v in ia if p=='INIT'),None)
        comps=[(p,v) for p,v in ia if p=='COMP' and int(v[1])==1]
        if init is None or not comps: continue
        # Mother direction on a COMP record is the outgoing photon direction.
        # For first primary COMP, find incoming direction from preceding primary record.
        first=comps[0][1]
        prior=[(p,v) for p,v in ia if v[0]<first[0] and (int(v[1])==1 or p=='INIT')]
        incoming=init[16:19]
        for p,v in prior:
            if p!='INIT' and int(v[7])==1: incoming=v[8:11]
        primary_before=[(p,v) for p,v in prior if p!='INIT']
        direct=int(first[2])==3 and not primary_before
        truth[eid]=(throw,angle(incoming,first[8:11]),direct,int(first[2]))
    rows=[]; nco=0; unmatched=0; invalid=0
    reader=M.MFileEventsTra()
    assert reader.Open(M.MString(str(RUNS/f'{name}.tra.gz')))
    while event:=reader.GetNextEvent():
        M.SetOwnership(event,True)
        if event.GetType()!=M.MPhysicalEvent.c_Compton: continue
        nco+=1
        if not event.IsGoodEvent():
            invalid+=1
            continue
        eid=int(event.GetId())
        if eid not in truth:
            unmatched+=1; continue
        throw,phi,direct,det=truth[eid]
        rows.append(dict(event_id=eid,throw_id=throw,true_angle_deg=phi,reconstructed_angle_deg=float(event.Phi()*180/math.pi),direct_first_compton_in_ge=int(direct),first_compton_detector_type=det,reconstructed_energy_keV=float(event.Ei()),reconstructed_hits=int(event.SequenceLength())))
    reader.Close()
    with gzip.open(BASE/f'{name}.angles.csv.gz','wt') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    residual=np.array([r['reconstructed_angle_deg']-r['true_angle_deg'] for r in rows])
    summary=dict(stored_sim_events=stored,revan_compton_records=nco,plotted_compton_events=len(rows),good_records_without_primary_compton=unmatched,records_failing_megalib_IsGoodEvent=invalid,direct_first_compton_in_ge=sum(r['direct_first_compton_in_ge'] for r in rows),median_residual_deg=float(np.median(residual)),absolute_residual_68_percentile_deg=float(np.quantile(abs(residual),.68)))
    return rows,summary

if __name__=='__main__':
    names=['300keV','1MeV_A','3MeV']
    results=[analyze(n) for n in names]
    plt.rcParams.update({'font.size':11,'axes.titlesize':13})
    fig,axes=plt.subplots(2,3,figsize=(15,9),layout='constrained',sharex=True,sharey=True)
    bins=np.linspace(0,180,91)
    hmax=max(np.histogram2d([r['true_angle_deg'] for r in rows],[r['reconstructed_angle_deg'] for r in rows],bins=(bins,bins))[0].max() for rows,_ in results)
    for j,((rows,s),title) in enumerate(zip(results,['300 keV','1 MeV','3 MeV'])):
        for i in range(2):
            selected=[r for r in rows if i==0 or r['direct_first_compton_in_ge']]
            ax=axes[i,j]
            h=ax.hist2d([r['true_angle_deg'] for r in selected],[r['reconstructed_angle_deg'] for r in selected],bins=(bins,bins),norm=LogNorm(vmin=1,vmax=hmax),cmap='magma',cmin=1)
            ax.plot([0,180],[0,180],color='#54d6d0',lw=1,ls='--')
            ax.set(xlim=(0,180),ylim=(0,180),aspect='equal',xticks=[0,45,90,135,180],yticks=[0,45,90,135,180])
            ax.set_title(f'{title} | N = {len(selected):,}')
            if i==1: ax.set_xlabel('True Compton angle (degrees)')
            if j==0: ax.set_ylabel(('All matched physical Compton records\n' if i==0 else 'First interaction: Compton in active Ge\n')+'Reconstructed angle (degrees)')
    fig.colorbar(h[3],ax=axes,label='Events per 2° × 2° bin (log scale)',shrink=.8)
    fig.suptitle('COSI DC3 · on-axis monoenergetic photons\n1,000,000 thrown photons per run · Cosima + DC3 Bayesian Revan',fontsize=17)
    fig.savefig(BASE/'compton_angle_density.png',dpi=180)
    fig.savefig(BASE/'compton_angle_density.pdf')
    summary={n:s for n,(_,s) in zip(names,results)}
    (BASE/'summary.json').write_text(json.dumps(summary,indent=2))
    print(json.dumps(summary,indent=2))
