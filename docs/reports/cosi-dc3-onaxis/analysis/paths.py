"""Repository-relative report paths, with optional reproduction destinations."""
from pathlib import Path
import os

REPORT=Path(__file__).resolve().parents[1]
BASE=Path(os.environ.get('COSI_REPORT_RESULTS',str(REPORT/'results'))).resolve()
RUNS=Path(os.environ.get('COSI_REPORT_RUNS',str(REPORT/'runs'))).resolve()
BASE.mkdir(parents=True,exist_ok=True)

def load_megalib():
    import ROOT
    checkout=Path(__file__).resolve().parents[4]
    library=Path(os.environ.get('MEGALIB',str(checkout)))/'lib/libMEGAlib.so'
    if ROOT.gSystem.Load(str(library))<0:
        raise RuntimeError(f'Cannot load MEGAlib library: {library}')
    return ROOT
