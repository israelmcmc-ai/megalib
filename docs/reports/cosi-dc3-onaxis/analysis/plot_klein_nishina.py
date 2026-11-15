"""Compare selected COSI Phi densities with angle-marginalized Klein-Nishina."""
from pathlib import Path
import csv, gzip, json, base64
import numpy as np
from scipy.integrate import quad
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from paths import BASE
MEC2=510.99895
def kn_shape_radian(phi,energy):
    ratio=1/(1+energy/MEC2*(1-np.cos(phi)))
    return ratio**2*(ratio+1/ratio-np.sin(phi)**2)*np.sin(phi)

def integrated_sigma_over_pi_re2(energy):
    a=energy/MEC2
    return 2*((1+a)/a**2*(2*(1+a)/(1+2*a)-np.log1p(2*a)/a)+np.log1p(2*a)/(2*a)-(1+3*a)/(1+2*a)**2)

plt.rcParams.update({'font.size':11,'axes.titlesize':13})
fig,axes=plt.subplots(2,3,figsize=(15,9),layout='constrained',sharex=True,sharey='col')
bins=np.linspace(0,180,37)
width=np.diff(bins)
grid=np.linspace(0,180,1801)
summaries={}
for j,(name,energy,title) in enumerate(zip(['300keV','1MeV_A','3MeV'],[300,1000,3000],['300 keV','1 MeV','3 MeV'])):
    norm=quad(kn_shape_radian,0,np.pi,args=(energy,),epsabs=1e-12)[0]
    analytic=integrated_sigma_over_pi_re2(energy)
    assert np.isclose(norm,analytic,rtol=1e-9)
    pdf=kn_shape_radian(np.deg2rad(grid),energy)/norm*np.pi/180
    assert np.isclose(np.trapezoid(pdf,grid),1,atol=1e-5)
    with gzip.open(BASE/f'{name}.angles.csv.gz','rt') as f: rows=list(csv.DictReader(f))
    summaries[name]={}
    expected=np.array([quad(kn_shape_radian,np.deg2rad(a),np.deg2rad(b),args=(energy,))[0]/norm for a,b in zip(bins[:-1],bins[1:])])
    assert np.isclose(expected.sum(),1)
    peak=float(pdf.max())
    for i in range(2):
        group=[r for r in rows if (int(r['reconstructed_hits'])==2 if i==0 else int(r['reconstructed_hits'])>2)]
        n=len(group)
        rec=np.array([float(r['reconstructed_angle_deg']) for r in group])
        truth=np.array([float(r['true_angle_deg']) for r in group])
        hrec,_=np.histogram(rec,bins=bins)
        htrue,_=np.histogram(truth,bins=bins)
        assert hrec.sum()==htrue.sum()==n
        peak=max(peak,float((hrec/(n*width)).max()),float((htrue/(n*width)).max()))
        ax=axes[i,j]
        ax.stairs(hrec/(n*width),bins,color='#1769aa',lw=1.8,label='Revan reconstructed Phi')
        ax.stairs(htrue/(n*width),bins,color='#d97706',lw=1.4,label='True Phi, same selected events')
        ax.plot(grid,pdf,color='#222222',ls='--',lw=2,label='Klein–Nishina × sin(Phi)')
        ax.set_title(f'{title} | N = {n:,}')
        ax.set(xlim=(0,180),ylim=(0,None),xticks=[0,30,60,90,120,150,180])
        ax.grid(axis='y',alpha=.18)
        if i==1: ax.set_xlabel('Compton angle Phi (degrees)')
        if j==0: ax.set_ylabel(('Exactly 2 reconstructed hits\n' if i==0 else '>2 reconstructed hits\n')+'Probability density (per degree)')
        summaries[name]['2 hits' if i==0 else '>2 hits']={'events':n,'bin_edges_deg':bins.tolist(),'reconstructed_probability_density_per_deg':(hrec/(n*width)).tolist(),'selected_truth_probability_density_per_deg':(htrue/(n*width)).tolist(),'klein_nishina_bin_probability':expected.tolist()}
    print(f'{title}: integrated Klein-Nishina numerical/analytic = {norm/analytic:.12f}')
    assert peak < 0.035
    axes[0,j].set_ylim(0,0.035)
handles,labels=axes[0,0].get_legend_handles_labels()
fig.legend(handles,labels,loc='outside lower center',ncols=3,frameon=False)
fig.suptitle('COSI DC3 · Phi distributions vs. Klein–Nishina\nEach distribution normalized to unit area · 5° histogram bins · no photopeak cut',fontsize=17)
fig.savefig(BASE/'phi_klein_nishina.png',dpi=180)
fig.savefig(BASE/'phi_klein_nishina.pdf')
(BASE/'phi_klein_nishina_data.json').write_text(json.dumps(summaries,indent=2))
encoded=base64.b64encode((BASE/'phi_klein_nishina.png').read_bytes()).decode()
fragment='<div id="cosi-phi-klein-nishina"><img style="display:block;width:100%;height:auto" alt="Normalized Phi distributions at 300 keV, 1 MeV and 3 MeV. Top row: two reconstructed hits. Bottom row: more than two reconstructed hits. Blue: Revan reconstructed Phi. Orange: true Phi of the same selected events. Dashed black: free-electron Klein-Nishina per angle, including the sine Jacobian. Five-degree histogram bins, no photopeak cut." src="data:image/png;base64,'+encoded+'"></div>\n'
assert len(fragment.encode())<1000000
(BASE/'phi-klein-nishina.html').write_text(fragment)
assert (BASE/'phi-klein-nishina.html').read_text()==fragment
