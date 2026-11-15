"""Single-factor envelope matching; this is not an absolute efficiency."""
from pathlib import Path
import json, base64
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from paths import BASE
data=json.loads((BASE/'phi_klein_nishina_data.json').read_text())
plt.rcParams.update({'font.size':11,'axes.titlesize':13})
fig,axes=plt.subplots(2,3,figsize=(15,9),layout='constrained',sharex=True,sharey=True)
summary={}
global_peak=0
for j,(name,title) in enumerate(zip(['300keV','1MeV_A','3MeV'],['300 keV','1 MeV','3 MeV'])):
    summary[name]={}
    for i,group in enumerate(['2 hits','>2 hits']):
        d=data[name][group]
        edges=np.array(d['bin_edges_deg'])
        widths=np.diff(edges)
        expected=np.array(d['klein_nishina_bin_probability'])/widths
        truth=np.array(d['selected_truth_probability_density_per_deg'])
        reconstructed=np.array(d['reconstructed_probability_density_per_deg'])
        reference=int(np.argmax(truth/expected))
        scale=float(expected[reference]/truth[reference])
        scaled_truth=scale*truth
        scaled_reconstructed=scale*reconstructed
        relative_survival=scaled_truth/expected
        assert np.all(relative_survival>=0) and np.all(relative_survival<=1+1e-12)
        assert np.isclose(relative_survival[reference],1)
        global_peak=max(global_peak,expected.max(),scaled_truth.max(),scaled_reconstructed.max())
        ax=axes[i,j]
        ax.stairs(expected,edges,baseline=scaled_truth,fill=True,color='#d97706',alpha=.14)
        ax.stairs(scaled_reconstructed,edges,color='#1769aa',lw=1.8,label='Revan Phi · same scale factor')
        ax.stairs(scaled_truth,edges,color='#d97706',lw=1.6,label='True Phi · envelope matched')
        ax.stairs(expected,edges,color='#222222',ls='--',lw=2,label='Klein–Nishina reference')
        ax.set_title(f'{title} | N = {d["events"]:,}')
        ax.set(xlim=(0,180),xticks=[0,30,60,90,120,150,180])
        ax.grid(axis='y',alpha=.18)
        if i==1: ax.set_xlabel('Compton angle Phi (degrees)')
        if j==0: ax.set_ylabel(('Exactly 2 reconstructed hits\n' if i==0 else '>2 reconstructed hits\n')+'Relative density (per degree)')
        summary[name][group]={'events':d['events'],'scale_applied_to_both_histograms':scale,'reference_bin_deg':edges[reference:reference+2].tolist(),'reference_bin_true_event_count':int(round(truth[reference]*widths[reference]*d['events'])),'bin_edges_deg':edges.tolist(),'true_relative_survival':relative_survival.tolist(),'true_relative_loss':(1-relative_survival).tolist()}
assert global_peak<.02
axes[0,0].set_ylim(0,.02)
handles,labels=axes[0,0].get_legend_handles_labels()
fig.legend(handles,labels,loc='outside lower center',ncols=3,frameon=False)
fig.suptitle('COSI DC3 · Phi distributions with relative losses\nOne scale factor per panel · true-Phi envelope matched to Klein–Nishina · 5° bins',fontsize=17)
fig.savefig(BASE/'phi_relative_loss.png',dpi=180)
fig.savefig(BASE/'phi_relative_loss.pdf')
(BASE/'phi_relative_loss_scaling.json').write_text(json.dumps(summary,indent=2))
encoded=base64.b64encode((BASE/'phi_relative_loss.png').read_bytes()).decode()
fragment='<div id="cosi-phi-relative-loss"><img style="display:block;width:100%;height:auto" alt="COSI Phi distributions at 300 keV, 1 MeV and 3 MeV, split into exactly two and more than two reconstructed hits. Each true-Phi histogram is scaled by one constant to touch the bin-integrated Klein-Nishina reference in the bin with the largest true-to-expected ratio. The same factor scales Revan Phi. Shading shows the gap between true Phi and the reference. These are relative losses, not absolute efficiencies; normalization is sensitive to counting fluctuations." src="data:image/png;base64,'+encoded+'"></div>\n'
assert len(fragment.encode())<1000000
(BASE/'phi-relative-loss.html').write_text(fragment)
assert (BASE/'phi-relative-loss.html').read_text()==fragment
print(json.dumps({n:{g:{k:v for k,v in s.items() if k in ('scale_applied_to_both_histograms','reference_bin_deg','reference_bin_true_event_count')} for g,s in groups.items()} for n,groups in summary.items()},indent=2))
