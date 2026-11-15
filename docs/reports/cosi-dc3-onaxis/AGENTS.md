# Maintaining this report

The user requested this report on branch `reports/cosi-dc3-onaxis-compton` and asked to update it as the analysis continues.

- For subsequent COSI angle analyses in this conversation, update `README.md`, the relevant analysis scripts, derived tables and figures, and the update history together.
- Keep the original SIM and TRA files in `runs/` unchanged. Put additional runs in new, named files and record their settings, seeds and software provenance.
- State angle definitions, event selections, hit multiplicity, binning and normalization beside each result. Separate observations from proposed physical explanations.
- Use `analysis/regenerate.sh` to check report scripts against the archived runs. New simulations default to the ignored `reproduction/` directory.
- After intentional report changes, run `analysis/verify_artifacts.py --update-manifest`, then `analysis/verify_artifacts.py`, inspect the resulting figures, and commit the report changes on this branch.
