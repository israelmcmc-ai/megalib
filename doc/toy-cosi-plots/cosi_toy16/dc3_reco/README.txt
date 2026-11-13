Native Revan Bayesian/classic comparison, with adjacent hit clustering

IMPORTANT RESPONSE PROVENANCE
The user-linked DC3 configuration selects MERCSRBayesian and names a Response.p1.mc.goodbad.rsp family on a private /discover/... filesystem. That exact DC3 response bundle is not present locally and was not found in the public DC3 data products or GitHub repository. The completed plots and timing comparison in this directory use the published COSI DC2 BayesianResponseO64.p1.mc.* tables from COSI-SMEX/DC2/Ancillary on the COSI public Wasabi bucket. They use the requested DC3 algorithm/clustering settings but are NOT an exact DC3 reproduction or a validated calibration for this monolithic toy. Transfer between geometries and detector resolutions can change reconstruction performance. Full source keys, sizes, ETags and SHA256 checksums are recorded in reference_dc2/manifest.json. The exact DC3 rerun needs the missing response family.

A separate experimental ToyTrain response was generated with the native MEGAlib responsecreator from an independent seed-42 simulation. Validation found that its six- and seven-site prior bins were empty, producing nonfinite corresponding classification scores. Those pilot results (ToyTrain*, results.*, compare.log) were rejected and are NOT used in the final plots, summary or timing. The validated final runs are named reference.* and use the downloaded response tables, which have nonzero good/bad training statistics for all multiplicities 2..7.

Retained simulation/response model
Same 16 x 16 x 16 cm Ge cube, five 2 cm BGO walls, 2 mm gap, open +z face. Reuse 100000-photon seed-43 662 keV full-footprint beam from ../revan4/area662.inc1.id1.sim.gz; no new evaluation transport. The response Gaussian energy and depth smearing, readout >=5 keV, unsmeared Ge trigger >=10 keV and ideal 50 keV per-panel BGO veto are exactly those in the prior plots. Per-event response seed [20261113, primary_id] is preserved. All 28543 veto-passing measured events with at least one readout hit are prepared BEFORE any multiplicity cut.

Native clustering
MERHitClusterizer.SetParameters(2,1.5): adjacent level 2, depth tolerance sigma 1.5. No event/coincidence clustering, no electron tracking. Every raw hit's detector/sensitive-volume coordinates are set to its actual measured position before clustering. This is important: earlier unclustered CSR code needed only a common Ge volume tag, whereas adjacency requires the per-hit coordinates in that volume. Energy and uncertainties are merged using MEGAlib's actual MRECluster implementation. Up to 7 interaction sites AFTER clustering are allowed. The common 2..7-site sample has 24817 events. Counts now refer to interaction sites, not individual raw strip deposits.

Native sequence reconstruction
Bayesian: MERCSRBayesian, quality range [0,1000], max 7, no forced start detector, response reference_dc2/BayesianResponseO64.p1.mc.goodbad.rsp and its companions. ClassicUndecidedHandling=3 in the DC3 XML is inactive under CSRAlgorithm=4.
Classic comparator: MERCSRChiSquare default simple statistic, same adjacent-clustered inputs, max 7, same quality range, same-detector events allowed, no forced start, ambiguous two-hit choice by larger Klein-Nishina (the same rule used earlier). The classic comparator intentionally keeps that prior tie-breaker rather than switching to KN-times-photo; all other preprocessing and multiplicity settings are matched.

Post-reconstruction cuts
Good sequence and finite score; valid first-scatter energy cosine; first and second reconstructed sites each >=10 keV; separation >=0.3 cm. The Compton angle uses first-site energy and SUM of every remaining site. There is NO photopeak/total-energy window and NO ARM cut. Test truth does not determine the chosen order or event selection. Known source +z is used only to compute displayed ARM. Final accepted counts: 20965 classic, 21464 Bayesian.

Truth comparison
The true angle is the actual change of primary-photon direction at its first Compton scatter in Ge, tracking prior COMP/RAYL direction changes. Events with no corresponding primary Ge Compton scatter have no reference angle and are excluded only from this diagnostic, not from reconstructed spectra or CDS. Every heatmap panel is normalized independently to unit integral, with a shared logarithmic color scale across the four panels.

Timing protocol
Both paths are compiled C++ calling the actual native MEGAlib libraries, in a single process. Five repetitions; alternate algorithm execution order between trials. Identical prebuilt clustered event objects are independently duplicated before each timed call. Timed CSR includes sequence search and native sequence construction; it excludes duplicate/input-object construction, file I/O, response loading, hit smearing and Python plotting. Common clustering is timed separately on fresh raw events in five repetitions. Aggregate CSR time is the median of per-trial SUMS over all multiplicities, not a sum of bin medians. Classical CSR median 6.738853961 s; Bayesian 17.263607927 s (2.5618x slower). Shared clustering median 0.096765663 s for 28543 raw input events. Median CSR+clustering: classic 6.835619624 s, Bayesian 17.358602528 s. These are not end-to-end full COSI pipeline timings and are not measurements of the unavailable DC3 table set.

Validation
- Synthetic adjacent and diagonal strip hits merge at level 2; distant and depth-separated hits do not. Cluster energy is conserved.
- Both algorithms receive identical 24817 unique event IDs, site counts and total energies.
- All reported good-sequence quality scores are finite, including 6/7-site events.
- Post-cut counts and rejection totals reconcile for each algorithm.
- Native clustering count histogram matches CSR input sample.
- Detector/source simulation data and test RNG remain independent of the rejected response-training sample.

Files
compare.cxx: native clustering + both native CSR methods + timing/output
prepare.py: measured-hit preparation with no multiplicity cut before clustering
reference.*.csv and reference.log: validated native outputs and five-run timings
reference_dc2/: published response tables and provenance manifest
summary.json and timing_summary.csv: final statistics
classic_events.npz, bayes_events.npz: reconstructed and truth-diagnostic arrays
energy_and_timing.png/.pdf: spectra and per-multiplicity timing comparison
bayes_cds.png/.pdf: Bayesian CDS and ARM, no photopeak cut
true_vs_reco_comparison.png/.pdf: classic/Bayesian truth-angle densities, split 2 versus 3..7 sites

Reproduction
Use default Python to run prepare.py. Source /workspace/.environment/activate-mega.sh, then compile compare.cxx using the same -D___LINUX___ -D___CLING___ ROOT flags and libMEGAlib link settings used in ../revan4/README.txt. Run compare measured_inputs.txt ../CosiToy16.geo.setup reference_dc2/BayesianResponseO64.p1.mc.goodbad.rsp reference. After it completes, use default Python with numpy/matplotlib to run analyze_reference.py. Source /workspace/.environment/activate-cosi.sh only for the published-response downloader (which uses the existing COSI public-data helper defaults without storing credentials in these deliverables).
