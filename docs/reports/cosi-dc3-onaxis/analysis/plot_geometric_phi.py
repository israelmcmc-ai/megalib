"""Use Revan positions for geometry; retain the existing validated matched sample."""
from pathlib import Path
import csv, gzip, json, math, base64
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
from paths import BASE, RUNS, load_megalib
M=load_megalib()

incoming=M.MVector(0.,0.,-1.)
names=['300keV','1MeV_A','3MeV']
results=[]
summary={}
for name in names:
    with gzip.open(BASE/f'{name}.angles.csv.gz','rt') as f:
        original={int(r['event_id']):r for r in csv.DictReader(f)}
    reader=M.MFileEventsTra()
    assert reader.Open(M.MString(str(RUNS/f'{name}.tra.gz')))
    matched=[]
    zero=0
    seen=set()
    while event:=reader.GetNextEvent():
        M.SetOwnership(event,True)
        eid=int(event.GetId())
        if eid not in original: continue
        assert event.GetType()==M.MPhysicalEvent.c_Compton and event.IsGoodEvent()
        assert eid not in seen
        seen.add(eid)
        r=original[eid]
        c1,c2=event.C1(),event.C2()
        direction=np.array([c2.X()-c1.X(),c2.Y()-c1.Y(),c2.Z()-c1.Z()])
        length=np.linalg.norm(direction)
        if length==0:
            zero+=1
            continue
        geo=math.degrees(math.acos(np.clip(-direction[2]/length,-1,1)))
        native=event.Dg().Angle(incoming)*180/math.pi
        assert abs(geo-native)<1e-7
        assert abs(float(r['reconstructed_angle_deg'])-event.Phi()*180/math.pi)<1e-9
        assert int(r['reconstructed_hits'])==event.SequenceLength()
        matched.append(dict(event_id=eid,true_angle_deg=float(r['true_angle_deg']),kinematic_angle_deg=float(event.Phi()*180/math.pi),geometric_angle_deg=geo,reconstructed_hits=int(event.SequenceLength())))
    reader.Close()
    assert seen==set(original)
    assert len(matched)+zero==len(original)
    groups=[[r for r in matched if (r['reconstructed_hits']==2 if i==0 else r['reconstructed_hits']>2)] for i in range(2)]
    assert sum(map(len,groups))==len(matched)
    results.append(groups)
    summary[name]={'two_hits':len(groups[0]),'more_than_two_hits':len(groups[1]),'excluded_coincident_first_two_positions':zero}
    with gzip.open(BASE/f'{name}.geometric_angles.csv.gz','wt') as f:
        w=csv.DictWriter(f,fieldnames=list(matched[0]));w.writeheader();w.writerows(matched)

bins=np.linspace(0,180,91)
comparisons=[('true_angle_deg','True Compton angle (degrees)','true-vs-geometric-phi','True Phi vs. geometric Phi'),('kinematic_angle_deg','Kinematic Compton angle (degrees)','kinematic-vs-geometric-phi','Kinematic Phi vs. geometric Phi')]
hmax=max(np.histogram2d([r[x] for r in group],[r['geometric_angle_deg'] for r in group],bins=(bins,bins))[0].max() for x,_,_,_ in comparisons for pair in results for group in pair)
plt.rcParams.update({'font.size':11,'axes.titlesize':13})
for x,xlabel,stem,title in comparisons:
    fig,axes=plt.subplots(2,3,figsize=(15,9),layout='constrained',sharex=True,sharey=True)
    for j,(energy,pair) in enumerate(zip(['300 keV','1 MeV','3 MeV'],results)):
        for i,rows in enumerate(pair):
            ax=axes[i,j]
            h=ax.hist2d([r[x] for r in rows],[r['geometric_angle_deg'] for r in rows],bins=(bins,bins),norm=LogNorm(vmin=1,vmax=hmax),cmap='magma',cmin=1)
            ax.plot([0,180],[0,180],color='#54d6d0',lw=1,ls='--')
            ax.set(xlim=(0,180),ylim=(0,180),aspect='equal',xticks=[0,45,90,135,180],yticks=[0,45,90,135,180])
            ax.set_title(f'{energy} | N = {len(rows):,}')
            if i==1: ax.set_xlabel(xlabel)
            if j==0: ax.set_ylabel(('Exactly 2 reconstructed hits\n' if i==0 else '>2 reconstructed hits\n')+'Geometric Compton angle (degrees)')
    fig.colorbar(h[3],ax=axes,label='Events per 2° × 2° bin (log scale)',shrink=.8)
    fig.suptitle(f'COSI DC3 · {title}\nGeometric Phi: incident −z direction vs. Revan C2 − C1',fontsize=17)
    fig.savefig(BASE/f'{stem}.png',dpi=180)
    fig.savefig(BASE/f'{stem}.pdf')
    encoded=base64.b64encode((BASE/f'{stem}.png').read_bytes()).decode()
    fragment=f'<div id="cosi-{stem}"><img style="display:block;width:100%;height:auto" alt="{title} density at 300 keV, 1 MeV and 3 MeV. Top row: exactly two reconstructed hits. Bottom row: more than two reconstructed hits. Geometric angle is measured between incoming minus-z direction and Revan first-to-second reconstructed position vector. Same validated truth-matched sample, no photopeak cut. Both figures share logarithmic event-count colors in two-degree bins." src="data:image/png;base64,'+encoded+'"></div>\n'
    assert len(fragment.encode())<1000000
    (BASE/f'{stem}.html').write_text(fragment)
    assert (BASE/f'{stem}.html').read_text()==fragment
    plt.close(fig)
(BASE/'geometric_phi_summary.json').write_text(json.dumps(summary,indent=2))
print(json.dumps(summary,indent=2))
print('Verified geometric angles against MEGAlib Dg().Angle(incident_direction). Shared color maximum:',hmax)
