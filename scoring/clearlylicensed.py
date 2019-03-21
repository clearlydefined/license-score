
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import cgi
from collections import OrderedDict
import csv
import json
import os
from subprocess import call
import sys
import traceback

try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse


import requests


current_dir = os.path.abspath(os.path.dirname(__file__))

"""
Process a list of popular software packages to compute a license clarity score.

This script performs the following steps:
1. download each package
2. extract the package archive
3. run a scan including score computation
4. collate all scans results in a CSV.
"""


def compute_license_score(input_csv='5000-packages-license-score-data.csv',
        output_csv='5000-packages-license-score-results-out.csv',
        base_dir=current_dir,
        do_fetch=True,
        do_extract=True):
    """
    Read the package data in the CSV at `input_csv` and write a CSV at
    `output_csv`. The `input_csv` must contain these columns: download_url and
    package URL fields (type, namespace, name, version).

    If `fetch` is True, fetch the Packages. Otherwise, assume Packages files are
    in the "packages" directory.
    If `scan` is True, scan the Packages. Otherwise, assume Packages scan files are
    in the "scans" directory.

    """
    downloads_dir = create_dir('downloads', base_dir=base_dir)
    extracts_dir = create_dir('extracts', base_dir=base_dir)
    scans_dir = create_dir('scans', base_dir=base_dir)

    # list of mappings
    results = []

    for i, package in enumerate(get_packages_data(csv_loc=input_csv)):
        download_url = package.get('download_url')
        pkg_type = package.get('type')
        pkg_name = package.get('name')
        print('===========================================================')
        print(i, 'Processing: ', download_url)

        archive_filename = package.get('filename')
        downloaded_archive_loc = os.path.join(downloads_dir, pkg_type, archive_filename)
        archive_extract_dir = archive_filename + '-extract'
        extracted_archive_loc = os.path.join(downloads_dir, pkg_type, archive_extract_dir)
        target_extracted_archive_loc = os.path.join(extracts_dir, pkg_type, archive_extract_dir)

        if do_fetch:
            fetch_file = fetch
            # filename MUST be present in CSV, otherwise the packages are fetched
            if archive_filename:
                if not os.path.exists(downloaded_archive_loc):
                    fetch_file = True
            else:
                fetch_file = True

            if fetch_file:
                try:
                    archive_filename = fetch_package(download_url, pkg_type, pkg_name, downloads_dir)
                except Exception:
                    package['scan_results_file'] = 'FAILED DOWNLOAD URL:\n{}'.traceback.format_exc()
                    results.append(package)
                    continue

        if not os.path.exists(downloaded_archive_loc):
            # things did not download alright
            continue

        if do_extract:
            extract(downloaded_archive_loc)

        # move the extracts to an extract dir
        if os.path.exists(extracted_archive_loc):
            os.rename(extracted_archive_loc, target_extracted_archive_loc)

        # TODO: fix key files location
        if type == 'gem':
            # we need to move files to root locations. Either we delete some (checksums, and archives after extraction...
            # remove checksums?
            pass

        if type == 'maven':
            # get META-INF/maven bits
            # the shape is:
            # META-INF/maven/<dotted-gid>/<aid>/pom.xml
            # META-INF/maven/<dotted-gid>/<aid>/pom.properties
            pass

        json_scan_loc = os.path.join(scans_dir, pkg_type, archive_filename + '-clarity.json')
        csv_scan_loc = os.path.join(scans_dir, pkg_type, archive_filename + '-clarity.csv')
        if not os.path.exists(json_scan_loc):
            try:
                scan(target_extracted_archive_loc, json_scan_loc, csv_scan_loc)
            except KeyboardInterrupt:
                break
            except Exception:
                pass

        scan_result={}
        if os.path.exists(json_scan_loc):
            with open(json_scan_loc, 'rb') as scanned:
                scan_result = json.load(scanned, object_pairs_hook=OrderedDict)

        license_score = scan_result.get('license_clarity_score', {})
        package.update(license_score)

        package['scan_results_file'] = json_scan_loc
        results.append(package)

    headers = results[0].keys()
    with open(output_csv, 'wb') as outfile:
        dict_writer = csv.DictWriter(outfile, headers)
        dict_writer.writeheader()
        dict_writer.writerows(results)


def fetch_package(url, download_dir):
    """
    Download the package at `url` in `download_dir` and return its filename.
    """
    MAX_RETRIES = 3
    success = False

    for i in range(MAX_RETRIES):
        response = requests.get(url, timeout=20)
        print('response.status_code:', response.status_code,)
        if response.status_code == 200:
            success = True
            break
        else:
            import time
            time.sleep(1)

    if not success:
        raise Exception(
            'Could not download content after ({MAX_RETRIES} retries):\n'.format(**locals())
            +traceback.format_exc())

    content_disposition = response.headers.get('content-disposition', '')
    _, params = cgi.parse_header(content_disposition)
    filename = params.get('filename')
    if not filename:
        # Using `response.url` in place of provided url since the former
        # will be more accurate in case of HTTP redirect.
        filename = os.path.basename(urlparse(response.url).path)

    filepath = os.path.join(download_dir, filename)

    with open(filepath, 'wb') as out:
        out.write(response.content)
    return filename


def extract(archive_loc):
    call(' '.join(['extractcode', str(archive_loc)]), shell=True)


def extract_shallow(archive_loc):
    call(' '.join(['extractcode', '--shallow', str(archive_loc)]), shell=True)


def scan(extracted_archive_loc, json_scan_loc, csv_scan_loc):
    call(' '.join([
        'scancode',
        '--copyright',
        '--license',
        '--license-text',
        '--license-diag',
        '--info',
        '--classify',
        '--timeout', '10',
        '--max-in-memory', '0',
        '--license-clarity-score',
        '--summary',
        '--summary-key-files',
         '-n', '2',
        '--json-pp', json_scan_loc,
        '--csv', csv_scan_loc,
         extracted_archive_loc
         ]),
        shell=True
    )


def get_packages_data(csv_loc='clearlylicensed.csv'):
    """
    Read the CSV at csv_loc and yield ordered mapping of package data
    """
    with open(csv_loc, 'rb') as csvfile:
        reader = csv.DictReader(csvfile)
        empty_template_row = OrderedDict((f, None) for f in reader.fieldnames)

        for row in reader:
            item = OrderedDict(empty_template_row)
            item.update(row)
            yield item


def create_dir(name, base_dir=current_dir):
    d = os.path.join(base_dir, name)
    try:
        os.makedirs(d)
    except OSError:
        if not os.path.isdir(d):
            raise
    return d


if __name__ == '__main__':

    fetch = True
    args = sys.argv[1:]
    if args:
        arg0 = args[0]
        if arg0 == '--no-fetch':
            do_fetch = False
            do_extract = False

    base_dir = os.environ.get('CLEARDATA', current_dir)

    compute_license_score(
        do_fetch=do_fetch, do_extract=do_extract, base_dir=base_dir)
