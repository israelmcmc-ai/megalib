Revan 2..4-hit plots and absolute effective area at 662 keV

This run uses the unchanged 16 cm Ge cube and five-sided 2 cm BGO shield, with 2 mm clearance and open +z face. New gamma transport is a uniform radius-15 cm disk beam at z=15 cm propagating along -z. 100000 unpolarized 662 keV photons, Cosima seed 43, LivermorePol physics. Beam area pi*15^2 = 706.858347 cm2 covers the complete Ge+BGO projected footprint. All primary events, including those missing the detector, are stored for the area denominator. This replaces the central-only radius-7.8 cm illumination for this effective-area run. Monte Carlo checks verify the sampled uniform-disk second moment, number of rays in the 16 cm square Ge aperture, radius bound and source-plane z.

Response and event preparation:
- Ge trigger: at least one raw deposited-energy channel >=10 keV.
- BGO veto: reject if any panel has integrated deposited energy >=50 keV; ideal BGO response.
- Per-hit Gaussian Ge energy sigma interpolates (0 keV,0.3 keV), (662,0.85), (2000,1.4).
- Readout: smeared hit energy >=5 keV. Virtual 1 mm x/y strip centers, z smeared by Gaussian sigma 0.05 cm.
- Response SeedSequence([20261113, primary_id]) makes each event's response independent of subsequent selection.
- Only BGO-veto-passing events with 2..4 readout Ge hits are sent to Revan. There is no truth-order, truth-origin-association or truth-energy-containment selection. No known source direction is given to sequence search. No hit clustering or electron tracking is added.

Actual Revan reconstruction:
reconstruct.cxx calls MERCSRChiSquare::FindComptonSequence, the same classic CSR method timed previously, via a thin public subclass. Default simple statistic; quality range [0,1000]; max 4 hits; no forced first detector; same-detector events allowed; Klein-Nishina two-hit ambiguity handling. Input has measured energies, positions and their uncertainties only; it has no truth first/second indices. All MREHit objects are tagged to the same known Ge detector volume; measured coordinates are left unmodified. External fixed resolutions prevent an additional response application. Output reconstructed.csv records the chosen first and second hit indices, good-event flag, quality and rejection code.

Cuts AFTER Revan:
- Good sequence, distinct first/second hits, valid Compton cosine.
- Both reconstructed first and second site energies >=10 keV.
- Reconstructed first-to-second distance >=0.3 cm.
- First-scatter angle uses Etotal and Eremaining=sum(all hit energies except first).
The energy distribution includes all passing reconstructed energies. CDS/ARM plots additionally select measured total energy in [657,667] keV. This is a measured photopeak window, not a truth-containment requirement. No ARM cut is applied to the CDS plots. Source direction +z is used only for plotting/diagnosing ARM.

Effective area:
Aeff = pi*(15 cm)^2 * N_selected / 100000.
One-sigma Monte Carlo statistical error = beam_area * sqrt(p*(1-p)/100000), p=N_selected/100000.
Denominator includes every generated primary, not only hits, triggers or reconstruction candidates.
These are on-axis single-energy effective areas of this toy detector and these explicit cuts, not an energy-dependent response curve or a calibration of the full COSI instrument. No dead time, live-time loss, accidental vetoes, charged backgrounds or detector-model systematic uncertainty is included. A separate optional photopeak plus |ARM|<=10 degree area is reported for an imaging-style selection. That optional angular cut does not enter the default photopeak area or CDS plots.

Key output counts:
17194 measured 2..4-hit events sent to Revan; 17181 good sequence flags.
12829 survive first-pair kinematic/energy/separation cuts.
11480 also satisfy the measured 657..667 keV photopeak window.
7206 additionally satisfy the OPTIONAL |ARM|<=10 degree window.

Effective areas:
Revan + first-pair cuts (all measured energies): 90.6829 +/- 0.7475 cm2.
Photopeak + same cuts: 81.1473 +/- 0.7126 cm2.
Optional photopeak + |ARM|<=10 degrees: 50.9362 +/- 0.5780 cm2.

Reproduction:
Use the existing activated MEGAlib/Geant4 environment to run cosima -s 43 area662.source. After transport, use default Python (numpy/matplotlib available) to run prepare.py. Compile reconstruct.cxx with the same toolchain/feature macros as MEGAlib, then run reconstruct measured_inputs.txt ../CosiToy16.geo.setup reconstructed.csv. Finally run analyze.py with default Python and a writable MPLCONFIGDIR.

Compile command after sourcing /workspace/.environment/activate-mega.sh:
"$CXX" -O3 -D___LINUX___ -D___CLING___ $(root-config --cflags) -I/workspace/megalib/include reconstruct.cxx -L/workspace/megalib/lib -lMEGAlib $(root-config --libs) -Wl,-rpath,/workspace/megalib/lib -o reconstruct

Outputs:
energy_and_effective_area.png/.pdf
compton_data_space.png/.pdf
summary.json, effective_area.csv, beam_validation.json
reconstructed.csv: actual Revan first-pair decisions, including rejected events
compton_events.csv: accepted Compton observables
revan_compton_events.npz: accepted broad and photopeak samples
measured_inputs.npz/.txt: all Revan inputs and incident-event bookkeeping

Checks:
All 100000 generated primary IDs are present and contiguous; candidate IDs exactly match measured cuts; Revan output IDs/hit counts match input; sequence indices valid and distinct; total energies agree between input and selection bookkeeping; Etotal=Efirst+Eremaining; no selected event has >4 hits; rejection counts reconcile; cut-stage counts monotonic; photopeak/CDS sample nonempty; beam covers full model; uniform illumination checks passed. Repository source files remain unchanged.

True versus reconstructed Compton-angle density plots:
plot_true_vs_reco.py matches the existing measured-photopeak Revan sample to SIM primary IDs. True angle is the angle between the incoming and outgoing primary-photon momentum directions at its FIRST COMPTON SCATTER IN GE. Incoming direction is updated through previous primary COMP/RAYL interactions, including those outside Ge. This is independent of the Revan hit ordering and measured energy angle. Events with no primary Ge Compton interaction have no such reference angle and are excluded (7 two-hit, 6 three/four-hit events). No further truth-quality cut is applied. Two-hit plot: 2517 events; three/four-hit plot: 8950. Each 3 degree x 3 degree density histogram integrates to one separately; both panels share the same logarithmic color normalization. Source/energy/BGO/first-pair cuts remain those of the existing photopeak sample, without an ARM cut.
Outputs: true_vs_reco_compton.png/.pdf, true_vs_reco_angles.csv/.npz, true_vs_reco_summary.json, true-vs-reconstructed-compton.html.

Plots without the photopeak cut:
Run plot_cds_no_photopeak.py and plot_true_vs_reco.py --no-photopeak. They reuse existing all_selected Revan results; no transport, detector response or reconstruction is repeated or changed. Outputs are in no_photopeak/. All 12829 events passing the prior Ge trigger, BGO veto, 2..4 readout-hit, Revan-sequence and first-pair cuts are used. There is no total measured-energy/photopeak or ARM cut. This adds 1349 events outside [657,667] keV relative to the photopeak plots. Counts: 3271 two-hit and 9558 three/four-hit events. True-angle comparison excludes only events without a primary Ge Compton interaction (7 and 6 respectively), leaving 3264 and 9552. The existing photopeak figures and their embedded views are preserved.
