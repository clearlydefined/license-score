# DownloadURL gathering utility

This Python utility will scrape various package manager APIs and top package lists, and
will output a csv file with package download URLs and pURL values for each package/package type.

** NOTE **: You will need to be in a scancode-toolkit virtualenv for this script
to work or to have scancode-toolkit installed and install the `requirements.txt` with pip.

To recreate the `top-packages-out.csv` score collection:

- `git clone https://github.com/clearlydefined/license-score`
- `git clone https://github.com/nexB/scancode-toolkit` and `cd scancode-toolkit`
- run `./configure` then `source bin/activate`
- `cd ../license-score/top-packages`
- `python fetch-top-package-download-urls.py`
