"""Investigate the low-kinematic-angle branch using the archived matched events."""
import csv, gzip, json, math, base64
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
from paths import BASE, RUNS, load_megalib

M=load_megalib()
MEC2=510.99895
# A common angular cut, derived for a fully absorbed 1 MeV two-hit event.
CUT_DEG=2*math.degrees(math.asin(MEC2/2000))
NAMES=['300keV','1MeV_A','3MeV']
ENERGIES=[300,1000,3000]

def records(path):
    block=[]
    with gzip.open(path,'rt') as f:
        for line in f:
            if line.strip() in ('SE','EN'):
                if block: yield block
                block=[]
            else: block.append(line.strip())
    if block: yield block

def load_table(path):
    with gzip.open(path,'rt') as f: return {int(r['event_id']):r for r in csv.DictReader(f)}

def enrich(name,energy):
    original=load_table(BASE/f'{name}.angles.csv.gz')
    geo=load_table(BASE/f'{name}.geometric_angles.csv.gz')
    rows={}
    for block in records(RUNS/f'{name}.tra.gz'):
        ids=[x for x in block if x.startswith('ID ')]
        if not ids: continue
        eid=int(ids[0].split()[1])
        if eid not in original: continue
        assert eid not in rows
        src=original[eid]
        eg,_,ee,_=map(float,next(x for x in block if x.startswith('CE ')).split()[1:])
        cd=list(map(float,next(x for x in block if x.startswith('CD ')).split()[1:]))
        hit_energies=[float(x.split()[5]) for x in block if x.startswith('CH ')]
        total=eg+ee
        phi=float(src['reconstructed_angle_deg'])
        # CE text is rounded relative to the cached native Phi, so use a finite tolerance.
        formula=math.degrees(math.acos(np.clip(1-MEC2*(1/eg-1/total),-1,1)))
        assert abs(phi-formula)<.02
        mult=int(src['reconstructed_hits'])
        reverse_cos=1-MEC2*(1/ee-1/total)
        boundary=2*math.degrees(math.asin(MEC2/(2*total))) if total>=MEC2/2 else 180.
        if mult==2:
            reverse_valid=bool(M.MComptonEvent.IsKinematicsOK(eg,ee))
            assert reverse_valid==(-1<reverse_cos<1)
            assert reverse_valid==(phi>=boundary)
        else:
            reverse_valid=None # Swapping first deposit and all remaining deposits is not a sequence reversal.
        r=dict(event_id=eid,reconstructed_hits=mult,kinematic_angle_deg=phi,true_angle_deg=float(src['true_angle_deg']),geometric_angle_deg=float(geo[eid]['geometric_angle_deg']),first_deposit_keV=ee,remaining_energy_keV=eg,reconstructed_energy_keV=float(src['reconstructed_energy_keV']),two_deposit_boundary_deg=boundary,reverse_order_physical=reverse_valid,reverse_order_phi_deg=math.degrees(math.acos(reverse_cos)) if reverse_valid else None,larger_first_deposit=(ee>=eg) if mult==2 else None,below_common_cut=phi<CUT_DEG,photopeak_within_2percent=abs(float(src['reconstructed_energy_keV'])/energy-1)<.02,has_cluster_at_1800_keV=any(abs(e-1800)<.1 for e in hit_energies),direct_first_compton_in_ge=bool(int(src['direct_first_compton_in_ge'])))
        rows[eid]=(r,np.array(cd[:3]),np.array(cd[6:9]))
    assert set(rows)==set(original)==set(geo)
    seen=set()
    for block in records(RUNS/f'{name}.inc1.id1.sim.gz'):
        ids=[x for x in block if x.startswith('ID ')]
        if not ids: continue
        eid=int(ids[0].split()[1])
        if eid not in rows: continue
        r,c1,c2=rows[eid]
        comps=[];ge_energy=0
        for x in block:
            if x.startswith('IA '):
                _,proc,rest=x.split(maxsplit=2)
                vals=list(map(float,rest.split(';')))
                if proc=='COMP' and vals[1]==1: comps.append(vals)
            elif x.startswith('HTsim '):
                vals=list(map(float,x.split(maxsplit=1)[1].split(';')))
                if vals[0]==3: ge_energy+=vals[4]
        assert comps
        first=np.array(comps[0][4:7])
        d1=float(np.linalg.norm(c1-first));d2=float(np.linalg.norm(c2-first))
        r.update(primary_compton_count=len(comps),simulated_ge_deposit_keV=ge_energy,raw_ge_within_2percent=abs(ge_energy/energy-1)<.02,ge_measurement_deficit_over_50keV=ge_energy-r['reconstructed_energy_keV']>50,true_first_to_C1_cm=d1,true_first_to_C2_cm=d2,true_first_nearer_C2_within_3mm=(d2<.3 and d2+.05<d1))
        seen.add(eid)
    assert seen==set(rows)
    values=[r for r,_,_ in rows.values()]
    with gzip.open(BASE/f'{name}.low_phi_diagnostics.csv.gz','wt') as f:
        w=csv.DictWriter(f,fieldnames=list(values[0]));w.writeheader();w.writerows(values)
    return values

def stats(rows):
    n=len(rows)
    two=[r for r in rows if r['reconstructed_hits']==2]
    badfull=[r for r in rows if r['photopeak_within_2percent'] and abs(r['kinematic_angle_deg']-r['true_angle_deg'])>20]
    return dict(events=n,photopeak_within_2percent=sum(r['photopeak_within_2percent'] for r in rows),raw_ge_within_2percent=sum(r['raw_ge_within_2percent'] for r in rows),kinematic_true_difference_over_20deg=sum(abs(r['kinematic_angle_deg']-r['true_angle_deg'])>20 for r in rows),reverse_order_unphysical=sum(not r['reverse_order_physical'] for r in two) if two else None,more_than_one_primary_compton=sum(r['primary_compton_count']>1 for r in rows),true_first_nearer_C2_within_3mm=sum(r['true_first_nearer_C2_within_3mm'] for r in rows),cluster_at_1800keV=sum(r['has_cluster_at_1800_keV'] for r in rows),ge_measurement_deficit_over_50keV=sum(r['ge_measurement_deficit_over_50keV'] for r in rows),photopeak_bad_events=len(badfull),photopeak_bad_with_multiple_primary_comptons=sum(r['primary_compton_count']>1 for r in badfull),photopeak_bad_true_first_nearer_C2=sum(r['true_first_nearer_C2_within_3mm'] for r in badfull))

allrows=[enrich(n,e) for n,e in zip(NAMES,ENERGIES)]
groups=[[[r for r in rows if r['below_common_cut'] and (r['reconstructed_hits']==2 if i==0 else r['reconstructed_hits']>2)] for i in range(2)] for rows in allrows]
summary={'common_cut_deg':CUT_DEG,'cut_definition':'Common Phi_kin < 2 asin(510.99895/(2*1000)) in all panels; nominal 1 MeV two-hit reverse-order boundary, not a universal cut.','proximity_definition':'True first primary COMP is <0.3 cm from reconstructed C2 and at least 0.05 cm nearer C2 than C1; this is a spatial signature, not full truth-order attribution.','energies':{}}
for name,energy,rows,pair in zip(NAMES,ENERGIES,allrows,groups):
    s={'nominal_two_hit_boundary_deg':2*math.degrees(math.asin(MEC2/(2*energy))),'nominal_equal_deposit_angle_deg':math.degrees(math.acos(1-MEC2/energy)),'threshold_18keV_nominal_min_phi_deg':math.degrees(math.acos(1-MEC2*18/(energy*(energy-18))))}
    ambiguous=[r for r in rows if r['reconstructed_hits']==2 and r['reverse_order_physical']]
    photo_ambiguous=[r for r in ambiguous if r['photopeak_within_2percent']]
    s['two_hit_order_choice']={'both_orders_physical':len(ambiguous),'both_orders_physical_larger_first':sum(r['larger_first_deposit'] for r in ambiguous),'photopeak_both_orders_physical':len(photo_ambiguous),'photopeak_both_orders_physical_larger_first':sum(r['larger_first_deposit'] for r in photo_ambiguous)}
    for i,label in enumerate(['2 hits','>2 hits']):
        total=[r for r in rows if (r['reconstructed_hits']==2 if i==0 else r['reconstructed_hits']>2)]
        s[label]={'below_common_cut':stats(pair[i]),'at_or_above_common_cut':stats([r for r in total if not r['below_common_cut']])}
    summary['energies'][name]=s

plt.rcParams.update({'font.size':11,'axes.titlesize':13})
bins=np.linspace(0,180,91)
hmax=max(np.histogram2d([r['true_angle_deg'] for r in g],[r['geometric_angle_deg'] for r in g],bins=(bins,bins))[0].max() for pair in groups for g in pair)
fig,axes=plt.subplots(2,3,figsize=(15,9),layout='constrained',sharex=True,sharey=True)
for j,(energy,pair) in enumerate(zip(['300 keV','1 MeV','3 MeV'],groups)):
    for i,rows in enumerate(pair):
        ax=axes[i,j]
        h=ax.hist2d([r['true_angle_deg'] for r in rows],[r['geometric_angle_deg'] for r in rows],bins=(bins,bins),norm=LogNorm(vmin=1,vmax=max(2,hmax)),cmap='magma',cmin=1)
        ax.plot([0,180],[0,180],color='#54d6d0',lw=1,ls='--')
        ax.set(xlim=(0,180),ylim=(0,180),aspect='equal',xticks=[0,45,90,135,180],yticks=[0,45,90,135,180])
        ax.set_title(f'{energy} | N = {len(rows):,}')
        if i==1: ax.set_xlabel('True Compton angle (degrees)')
        if j==0: ax.set_ylabel(('Exactly 2 reconstructed hits\n' if i==0 else '>2 reconstructed hits\n')+'Geometric Compton angle (degrees)')
fig.colorbar(h[3],ax=axes,label='Events per 2° × 2° bin (log scale)',shrink=.8)
fig.suptitle(f'COSI DC3 · true Phi vs. geometric Phi · kinematic Phi < {CUT_DEG:.2f}°\nSame common angular cut at all energies · no photopeak cut',fontsize=17)
stem='true-vs-geometric-low-kinematic-phi'
fig.savefig(BASE/f'{stem}.png',dpi=180);fig.savefig(BASE/f'{stem}.pdf')
encoded=base64.b64encode((BASE/f'{stem}.png').read_bytes()).decode()
fragment=f'<div id="cosi-{stem}"><img style="display:block;width:100%;height:auto" alt="True Phi on x versus geometric Phi on y for kinematic Phi below {CUT_DEG:.2f} degrees, at 300 keV, 1 MeV and 3 MeV. Top row two reconstructed hits, bottom row more than two. No photopeak cut. The cut is the nominal 1 MeV two-hit energy-order boundary and is applied as a common cut at all energies." src="data:image/png;base64,'+encoded+'"></div>\n'
assert len(fragment.encode())<1000000
(BASE/f'{stem}.html').write_text(fragment)
assert (BASE/f'{stem}.html').read_text()==fragment
plt.close(fig)

# Show the event-dependent boundary rather than treating 30 degrees as universal.
fig,axes=plt.subplots(2,3,figsize=(15,9),layout='constrained')
energy_hist=[]
for rows,energy in zip(allrows,ENERGIES):
    two=[r for r in rows if r['reconstructed_hits']==2]
    energy_hist.append(np.histogram2d([r['reconstructed_energy_keV'] for r in two],[r['kinematic_angle_deg'] for r in two],bins=(np.linspace(0,energy*1.05,64),bins)))
vmax=max(h[0].max() for h in energy_hist)
for j,(rows,energy,title,hist) in enumerate(zip(allrows,ENERGIES,['300 keV','1 MeV','3 MeV'],energy_hist)):
    ax=axes[0,j]
    counts,xe,ye=hist
    mesh=ax.pcolormesh(xe,ye,np.ma.masked_less(counts.T,1),norm=LogNorm(vmin=1,vmax=vmax),cmap='magma',shading='flat')
    grid=np.linspace(MEC2/2,energy*1.05,1000)
    boundary=2*np.degrees(np.arcsin(MEC2/(2*grid)))
    ax.plot(grid,boundary,color='#16a6a1',lw=1.5,label='Reverse-order boundary')
    equal=np.degrees(np.arccos(np.clip(1-MEC2/grid,-1,1)))
    ax.plot(grid,equal,color='#8054a8',lw=1.3,ls='--',label='Equal energy deposits')
    ax.axvline(energy,color='#888888',ls=':',lw=1)
    ax.set(xlim=(0,energy*1.05),ylim=(0,180),xlabel='Reconstructed total energy (keV)',title=f'{title} · exactly 2 hits')
    if j==0: ax.set_ylabel('Kinematic Phi (degrees)')
    two=[r for r in rows if r['reconstructed_hits']==2]
    for valid,color,label in [(False,'#1769aa','Reverse order unphysical'),(True,'#d97706','Both energy orders physical')]:
        vals=[r['kinematic_angle_deg'] for r in two if r['reverse_order_physical']==valid]
        axes[1,j].hist(vals,bins=bins,histtype='step',color=color,lw=1.6,label=label)
    alternative=[r['reverse_order_phi_deg'] for r in two if r['reverse_order_physical']]
    axes[1,j].hist(alternative,bins=bins,histtype='step',color='#666666',ls=':',lw=1.3,label='Alternative physical order')
    nominal=summary['energies'][NAMES[j]]['nominal_two_hit_boundary_deg']
    equal_nominal=summary['energies'][NAMES[j]]['nominal_equal_deposit_angle_deg']
    axes[1,j].axvline(nominal,color='#16a6a1',ls='--',lw=1.5,label='Nominal reverse-order boundary')
    axes[1,j].axvline(equal_nominal,color='#8054a8',ls='--',lw=1.3,label='Nominal equal-deposit angle')
    axes[1,j].set(xlim=(0,180),ylim=(0,None),xlabel='Kinematic Phi (degrees)',title=f'Nominal boundaries: {nominal:.2f}° and {equal_nominal:.2f}°')
    axes[1,j].grid(axis='y',alpha=.18)
    if j==0: axes[1,j].set_ylabel('Events per 2° bin')
fig.colorbar(mesh,ax=list(axes[0]),label='Events per energy–angle bin (log)',shrink=.75)
handles,labels=axes[1,0].get_legend_handles_labels()
fig.legend(handles,labels,loc='outside lower center',ncols=3,frameon=False)
fig.suptitle('COSI DC3 · two-hit energy-order ambiguity and Bayesian order choice\nCurves: reverse-order boundary and equal-deposit angle vs. reconstructed total energy',fontsize=17)
fig.savefig(BASE/'two-hit-ambiguity-boundary.png',dpi=180)
fig.savefig(BASE/'two-hit-ambiguity-boundary.pdf')
plt.close(fig)
(BASE/'low_phi_summary.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary,indent=2))
