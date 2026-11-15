#!/usr/bin/env bash
set -euo pipefail
analysis_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
python_bin=${PYTHON:-python}
"$python_bin" "$analysis_dir/analyze.py"
"$python_bin" "$analysis_dir/plot_hit_split.py"
"$python_bin" "$analysis_dir/plot_klein_nishina.py"
"$python_bin" "$analysis_dir/plot_phi_relative_loss.py"
"$python_bin" "$analysis_dir/plot_geometric_phi.py"
