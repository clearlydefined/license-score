# clearlylicensed-test Utility

This Python utility will take the `download_url` values from 
`5000-packages-license-score-data.csv`, and will download  and extract them, 
then scan them with scancode using specific options to compute a score.

The scans are kept in the `scans` dir and the downloaded packages are in `downloads`.

The `license_score` data from the scan results will be collated and two final
data files will be created:

- 5000-packages-license-score-results-out.csv that contains the license score for each package
- 5000-packages-license-score-results-aggregates.csv that contains the aggregated score tables

** NOTE **: You will need to be in a scancode-toolkit virtualenv for this script
to work or to have scancode-toolkit installed and install the `requirements.txt` with pip.

To recreate the data from scratch use this:

- `git clone https://github.com/clearlydefined/license-score`
- `git clone https://github.com/nexB/scancode-toolkit` and `cd scancode-toolkit`
- run `./configure` then `source bin/activate`
- `cd ../license-score/scoring`
- run `pip install -r requirements.txt`
- run `python clearlylicensed.py`

This will take a long time.
You can edit the script to determine whether to fetch/extract/scan/score or not.
