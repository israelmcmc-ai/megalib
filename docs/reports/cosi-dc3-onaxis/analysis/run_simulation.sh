#!/usr/bin/env bash
# Requires cosima/revan on PATH and Python with ROOT, NumPy, SciPy and Matplotlib.
set -euo pipefail
analysis_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
report_dir=$(cd -- "$analysis_dir/.." && pwd)
export COSI_REPORT_RUNS=${COSI_REPORT_RUNS:-"$report_dir/reproduction/runs"}
export COSI_REPORT_RESULTS=${COSI_REPORT_RESULTS:-"$report_dir/reproduction/results"}
python_bin=${PYTHON:-python}
"$python_bin" - "$report_dir" <<'PY'
from pathlib import Path
import os,re,sys
report=Path(sys.argv[1])
runs=Path(os.environ['COSI_REPORT_RUNS']).resolve()
runs.mkdir(parents=True,exist_ok=True)
model=report/'inputs/massmodel/COSISMEX.sim.geo.setup'
template=report/'inputs/dc3/SMEXv12.Continuum.HEALPixO3.binnedimaging.revan.cfg'
response=report/'inputs/dc3/Revan/Response.p1.mc.goodbad.rsp'
for name in ['300keV','1MeV_A','3MeV']:
    if any(runs.glob(name+'.*')):
        raise FileExistsError(f'Choose an empty COSI_REPORT_RUNS directory: existing {name} output')
cfg=re.sub(r'(<BayesianComptonFile>).*?(</BayesianComptonFile>)',lambda m:m[1]+str(response)+m[2],template.read_text())
(runs/'effective.revan.cfg').write_text(cfg)
for name,energy in [('300keV',300),('1MeV_A',1000),('3MeV',3000)]:
    source=(report/'runs'/f'{name}.source').read_text()
    source=re.sub(r'^Geometry\s+.*$',lambda m:'Geometry '+str(model),source,flags=re.M)
    source=re.sub(r'^OnAxis.FileName\s+.*$',lambda m:'OnAxis.FileName '+str(runs/name),source,flags=re.M)
    (runs/f'{name}.source').write_text(source)
print(runs)
PY
for spec in '300keV 30101' '1MeV_A 100101' '3MeV 300101'; do
  read -r case_name case_seed <<< "$spec"
  cosima -s "$case_seed" "$COSI_REPORT_RUNS/$case_name.source" > "$COSI_REPORT_RUNS/$case_name.cosima.log" 2>&1
  revan -n -a -c "$COSI_REPORT_RUNS/effective.revan.cfg" \
    -g "$report_dir/inputs/massmodel/COSISMEX.analysis.geo.setup" \
    -f "$COSI_REPORT_RUNS/$case_name.inc1.id1.sim.gz" \
    -o "$COSI_REPORT_RUNS/$case_name.tra.gz" > "$COSI_REPORT_RUNS/$case_name.revan.log" 2>&1
done
bash "$analysis_dir/regenerate.sh"
