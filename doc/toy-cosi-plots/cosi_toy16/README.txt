Fast COSI-inspired Ge + BGO toy

Geometry:
- One 16 x 16 x 16 cm active germanium cube centered at the origin.
- Five 2 cm thick BGO slabs on +/-x, +/-y, and -z. +z is open.
- 0.2 cm (2 mm) vacuum clearance between Ge and BGO. Slab edges meet without overlapping; outside width 20.4 cm.
- Germanium uses virtual 1 mm x/y strips and offline 0.5 mm sigma depth smearing. The monolithic active block and 5 slabs are six simple transport volumes. There are no individual COSI modules, cryostat, support structures, optical photons, or charge transport.

Gamma demonstration:
30000 unpolarized 662 keV primary photons, seed 42. Parallel -z beam from z=15 cm uniformly illuminating a radius-7.8 cm disk. All initial rays intersect Ge. LivermorePol electromagnetic physics. 18.4598 CPU seconds in this environment (startup excluded). No direct timing comparison against the full COSI mass model was made.

Veto:
Accept if at least one Ge channel has deposited energy >=10 keV AND all five BGO panels have deposited energy <50 keV each. Panel energy is integrated over one simulated primary event, with ideal BGO response. Ge pulse-height and depth smearing are applied offline with response seed 20261113; energy sigma linearly interpolates (0 keV,0.3 keV), (662,0.85), (2000,1.4). Measured spectrum sums channels with smeared energy >=5 keV. Veto/Ge trigger decisions use unsmeared deposited energy, consistently in diagnostic selection and saved-event filtering.

IMPORTANT Cosima behavior:
Cosima explicitly disables thresholds and vetoes at pretrigger time (MCDetectorConstruction.cc, IgnoreVetoes(true), IgnoreThresholds(true)). PreTriggerMode Full is NOT an applied BGO veto. Geometry declares all five veto triggers for downstream MEGAlib use, and apply_veto.py explicitly enforces the above deposited-energy rule before writing accepted.sim.gz. Full pretrigger retains Ge-hit events, saving unnecessary output. Diagnostic mode preserves everything for comparing with and without the veto in one exposure.

Run:
./run_fast.sh
This runs production.source and writes production.accepted.sim.gz with the veto applied. Simulation and all scripts are local to this task; repository source files were not modified.
To rebuild the fixed geometry/source definitions: python build_model.py
To reproduce the diagnostic: source /workspace/.environment/activate-mega.sh; cosima -s 42 diagnostic.source
Filter: python apply_veto.py diagnostic.inc1.id1.sim.gz accepted.sim.gz
Plot: MPLCONFIGDIR=/workspace/work/mpl-cache python analyze.py
The plot script uses numpy/matplotlib from the default Python environment (activation of the C++ transport environment is not required).

Outputs:
results/geometry_energy_veto.png and .pdf
results/compton_data_space.png and .pdf
results/event_table.csv and compton_events.csv
results/events.npz and summary.json
accepted.sim.gz is the actual veto-filtered 30000-primary demonstration, with 25753 accepted events, original primary IDs, original transport truth and hits, and original TE/TS exposure metadata. Stored-event IDs are renumbered contiguously.

Validation:
Analytic bounding-box overlap check for all 6 volumes; separate Geant4 overlap-check run (1000 sampled points per volume, 1e-4 cm tolerance) completed without reported overlaps. Energy deposited in Ge+BGO agrees with SIM ED to <0.02 keV. Accepted output is re-read and every saved event must pass the Ge trigger and fail all BGO vetoes. A 3000-primary Full-pretrigger run plus filter is checked against the matching diagnostic primary IDs.

Compton plots (updated to include >2 hits):
Full-energy events passing the BGO veto and with >=2 readout Ge hits are eligible. Simulation truth identifies the first primary-photon Compton interaction and the next primary-photon Compton/photoelectric interaction and maps them to recorded hits. Initial or intervening primary Rayleigh scattering, missing/split first-pair hits and a first-site recoil energy merged with a later primary interaction are excluded. Later sites do not need ordering. First two sites must each have >=10 keV, measured total must be within 5 keV of 662, first separation >=0.3 cm, valid Compton cosine. Remaining photon energy is the SUM OF ALL READOUT HIT ENERGIES EXCEPT THE FIRST, never only the second-hit energy. The source direction is not used for sequencing; it is used only when displaying ARM.

The retained sample has 14551 events, including 12775 with >2 readout hits and multiplicities up to 13. This is a clean truth-selected sample, not a reconstruction efficiency. Directions use COSIPY convention d=(r1-r2)/|r1-r2|, psi=acos(d_z), chi=atan2(d_y,d_x), phi from measured energies. Source +z implies phi approximately psi; ARM=phi-psi. Response random numbers now use per-event SeedSequence([20261113, primary_id]) so that broadening event selection does not alter another event's detector response. This changes individual smear realizations relative to the earlier global-stream run, while preserving the response model.

Reconstruction benchmark:
benchmark_revan.cxx calls the actual MEGAlib MERCSRChiSquare::FindComptonSequence implementation through a thin subclass. It searches without truth order; classic default simple statistic, Klein-Nishina handling for ambiguous two-hit events, no forced first detector, same-detector events allowed, maximum 7 hits. The truth path only needs the first two truth indices and computes the Compton quantities using total-minus-first energy. Both paths receive identical preconstructed measured MREHit/MRERawEvent objects; hit energies, position and energy uncertainties match the Python analysis. No clustering, electron tracking, transport, file reading, detector smearing, truth-origin mapping, event-object construction or output writing is timed. This is an in-memory sequencing/Compton-quantity benchmark, not a full Revan CLI or full COSI pipeline benchmark. There is no known source direction input to the sequence search.

Five repetitions are measured by hit multiplicity; median times and an aggregate median over per-trial totals are saved in results/revan_timing.csv. The C++ truth shortcut is repeated 200 passes per trial and divided by 200 to resolve its short execution time. Separate benchmark_python.py measures the actual Python observables function on exactly the same preloaded 2..7-hit inputs, using five repetitions. It is run after the C++ benchmark to avoid CPU contention in its final timing. The analysis retains >=8-hit events, but those are excluded from the sequencing benchmark (379 events); exhaustive search cost increases factorially and the configured benchmark limit is 7. There are 14172 common benchmark events.

Compile using the activated MEGAlib toolchain and the same library feature macros:
source /workspace/.environment/activate-mega.sh
"$CXX" -O3 -D___LINUX___ -D___CLING___ $(root-config --cflags) -I/workspace/megalib/include benchmark_revan.cxx -L/workspace/megalib/lib -lMEGAlib $(root-config --libs) -Wl,-rpath,/workspace/megalib/lib -o benchmark_revan
./benchmark_revan results/benchmark_inputs.txt CosiToy16.geo.setup results/revan_timing.csv
python benchmark_python.py
python test_reconstruction.py

Physical scope:
BGO detects deposited energy from escaping photons; it is not a truth-based incomplete-energy cut. Escape through the open top, subthreshold BGO deposits, and photons traversing BGO remain possible. The same energy-based rule can later veto charged-particle deposits, but this gamma-only demonstration does not validate charged-particle or hadronic-background response. No accidental coincidences, finite coincidence window, pile-up, BGO scintillation statistics or dead time are included. Ideal full-energy retention in this run is expected under those assumptions.

Final measured reconstruction timing (five repeats, 14172 common 2..7-hit events): current Python truth-pair quantities 0.21953314 s median; actual Revan library classic sequence search + quantities 6.250241998 s median; 28.47x for this multiplicity mixture. This ratio excludes I/O, detector response, origin mapping and object setup. The separate C++ truth shortcut takes 0.003814904 s, isolating algorithm cost from Python overhead. These are not end-to-end speedups of a COSI analysis. Per-hit and trial timing records are retained in results.
