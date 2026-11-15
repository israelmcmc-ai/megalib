from analyze import analyze, BASE
import json, base64
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm

names=['300keV','1MeV_A','3MeV']
results=[analyze(n) for n in names]
bins=np.linspace(0,180,91)
groups=[[[r for r in rows if (r['reconstructed_hits']==2 if i==0 else r['reconstructed_hits']>2)] for i in range(2)] for rows,_ in results]
for (rows,_),group in zip(results,groups):
    assert len(group[0])+len(group[1])==len(rows)
    assert all(r['reconstructed_hits']>=2 for r in rows)
hmax=max(np.histogram2d([r['true_angle_deg'] for r in g],[r['reconstructed_angle_deg'] for r in g],bins=(bins,bins))[0].max() for pair in groups for g in pair)
plt.rcParams.update({'font.size':11,'axes.titlesize':13})
fig,axes=plt.subplots(2,3,figsize=(15,9),layout='constrained',sharex=True,sharey=True)
counts={}
for j,(name,title,pair) in enumerate(zip(names,['300 keV','1 MeV','3 MeV'],groups)):
    counts[name]={'two_hits':len(pair[0]),'more_than_two_hits':len(pair[1])}
    for i,rows in enumerate(pair):
        ax=axes[i,j]
        h=ax.hist2d([r['true_angle_deg'] for r in rows],[r['reconstructed_angle_deg'] for r in rows],bins=(bins,bins),norm=LogNorm(vmin=1,vmax=hmax),cmap='magma',cmin=1)
        ax.plot([0,180],[0,180],color='#54d6d0',lw=1,ls='--')
        ax.set(xlim=(0,180),ylim=(0,180),aspect='equal',xticks=[0,45,90,135,180],yticks=[0,45,90,135,180])
        ax.set_title(f'{title} | N = {len(rows):,}')
        if i==1: ax.set_xlabel('True Compton angle (degrees)')
        if j==0: ax.set_ylabel(('Exactly 2 reconstructed hits\n' if i==0 else '>2 reconstructed hits\n')+'Reconstructed angle (degrees)')
fig.colorbar(h[3],ax=axes,label='Events per 2° × 2° bin (log scale)',shrink=.8)
fig.suptitle('COSI DC3 · on-axis · split by reconstructed hit count\n1,000,000 thrown photons per energy · DC3 Bayesian Revan',fontsize=17)
fig.savefig(BASE/'compton_angle_hit_split.png',dpi=180)
fig.savefig(BASE/'compton_angle_hit_split.pdf')
(BASE/'hit_split_counts.json').write_text(json.dumps(counts,indent=2))
encoded=base64.b64encode((BASE/'compton_angle_hit_split.png').read_bytes()).decode()
fragment='<div id="cosi-compton-hit-split"><img style="display:block;width:100%;height:auto" alt="True versus Revan reconstructed Compton angle density at 300 keV, 1 MeV and 3 MeV. Top row: exactly two reconstructed hits. Bottom row: more than two reconstructed hits. Validated, truth-matched Compton events, without a photopeak energy cut. Shared logarithmic count scale in two-degree bins; dashed diagonal indicates agreement." src="data:image/png;base64,'+encoded+'"></div>\n'
assert len(fragment.encode())<1000000
(BASE/'compton-angle-hit-split.html').write_text(fragment)
assert (BASE/'compton-angle-hit-split.html').read_text()==fragment
print(json.dumps(counts,indent=2))
