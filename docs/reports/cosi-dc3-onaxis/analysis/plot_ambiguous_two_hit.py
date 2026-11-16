"""Both two-hit energy assignments must pass MEGAlib kinematics."""
import csv, gzip, json, base64
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
from paths import BASE, load_megalib

M=load_megalib()
names=['300keV','1MeV_A','3MeV']
groups=[]
summary={'selection':'Baseline validated truth-matched Compton sample; SequenceLength == 2; selected and reversed energy orders both pass MComptonEvent.IsKinematicsOK. No angular or photopeak cut.','angles':'Saved Revan ordering is used for both geometric and kinematic Phi; true Phi retains the original first-primary-COMP definition.','energies':{}}
for name in names:
    with gzip.open(BASE/f'{name}.low_phi_diagnostics.csv.gz','rt') as f:
        original=list(csv.DictReader(f))
    two=[r for r in original if int(r['reconstructed_hits'])==2]
    selected=[]
    for r in two:
        ee=float(r['first_deposit_keV']);eg=float(r['remaining_energy_keV'])
        assert M.MComptonEvent.IsKinematicsOK(ee,eg)
        ambiguous=bool(M.MComptonEvent.IsKinematicsOK(eg,ee))
        assert ambiguous==(r['reverse_order_physical']=='True')
        if ambiguous: selected.append(r)
    assert len({int(r['event_id']) for r in selected})==len(selected)
    groups.append(selected)
    summary['energies'][name]={'baseline_two_hit_events':len(two),'ambiguous_two_hit_events':len(selected),'photopeak_within_2percent':sum(r['photopeak_within_2percent']=='True' for r in selected),'selected_larger_first_deposit':sum(r['larger_first_deposit']=='True' for r in selected),'event_ids':[int(r['event_id']) for r in selected]}
    with gzip.open(BASE/f'{name}.ambiguous_two_hit.csv.gz','wt') as f:
        writer=csv.DictWriter(f,fieldnames=list(original[0]))
        writer.writeheader();writer.writerows(selected)

bins=np.linspace(0,180,91)
ys=[('geometric_angle_deg','Geometric Compton angle (degrees)'),('kinematic_angle_deg','Kinematic Compton angle (degrees)')]
hmax=max(np.histogram2d([float(r['true_angle_deg']) for r in rows],[float(r[y]) for r in rows],bins=(bins,bins))[0].max() for rows in groups for y,_ in ys)
plt.rcParams.update({'font.size':11,'axes.titlesize':13})
fig,axes=plt.subplots(2,3,figsize=(15,9),layout='constrained',sharex=True,sharey=True)
for j,(title,rows) in enumerate(zip(['300 keV','1 MeV','3 MeV'],groups)):
    for i,(y,ylabel) in enumerate(ys):
        ax=axes[i,j]
        h=ax.hist2d([float(r['true_angle_deg']) for r in rows],[float(r[y]) for r in rows],bins=(bins,bins),norm=LogNorm(vmin=1,vmax=max(2,hmax)),cmap='magma',cmin=1)
        ax.plot([0,180],[0,180],color='#54d6d0',lw=1,ls='--')
        ax.set(xlim=(0,180),ylim=(0,180),aspect='equal',xticks=[0,45,90,135,180],yticks=[0,45,90,135,180])
        ax.set_title(f'{title} | N = {len(rows):,}')
        if i==1: ax.set_xlabel('True Compton angle (degrees)')
        if j==0: ax.set_ylabel(ylabel)
fig.colorbar(h[3],ax=axes,label='Events per 2° × 2° bin (log scale)',shrink=.8)
fig.suptitle('COSI DC3 · exactly 2 reconstructed hits · both energy orders physical\nTop: true Phi vs. geometric Phi · bottom: true Phi vs. kinematic Phi · no photopeak cut',fontsize=17)
stem='ambiguous-two-hit-phi-comparisons'
fig.savefig(BASE/f'{stem}.png',dpi=180)
fig.savefig(BASE/f'{stem}.pdf')
(BASE/'ambiguous_two_hit_summary.json').write_text(json.dumps(summary,indent=2)+'\n')
encoded=base64.b64encode((BASE/f'{stem}.png').read_bytes()).decode()
fragment=f'<div id="cosi-{stem}"><img style="display:block;width:100%;height:auto" alt="Exactly two reconstructed hits with both energy orderings physical according to MEGAlib. Columns are 300 keV, 1 MeV and 3 MeV. True Phi is on x in all panels. Top row has geometric Phi on y; bottom row has Revan kinematic Phi on y. Same selected ordering and same event sample for both rows, no angular or photopeak cut. Shared logarithmic color scale, two-degree bins, dashed equal-angle diagonal." src="data:image/png;base64,'+encoded+'"></div>\n'
assert len(fragment.encode())<1000000
(BASE/f'{stem}.html').write_text(fragment)
assert (BASE/f'{stem}.html').read_text()==fragment
print(json.dumps({name:{k:v for k,v in s.items() if k!='event_ids'} for name,s in summary['energies'].items()},indent=2))
