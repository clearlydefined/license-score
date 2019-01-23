# clearlylicensed-test Utility

This Python utility will take the `download_url` values from `clearlylicensed.csv`, and will
download them, extract them, then scan them with scancode using specific options to compute a score. 

The `license_score` data from the scan results will then be added to the correct row in 
the output csv file: `clearlylicensed-out.csv`. 
These file names are hardcoded for now.

The scans are kept in the `scans` dir and the downloaded packages are in `packages`.


** NOTE **: You will need to be in a scancode-toolkit virtualenv for this script
to work or to have scancode-toolkit installed and install the `requirements.txt` with pip.

To recreate the `clearlylicensed-out.csv` score collection:

- `git clone https://github.com/clearlydefined/license-score`
- `git clone https://github.com/nexB/scancode-toolkit` and `cd scancode-toolkit`
- run `./configure` then `source bin/activate`
- `cd ../license-score/scoring`
- `python clearlylicensed-test.py`
