
from __future__ import print_function

from collections import OrderedDict
import csv
import json
import os
import glob
from subprocess import call

import requests


current_dir = os.path.dirname(__file__)


def create_dir(name, base_dir=current_dir):
    d = os.path.join(base_dir, name)
    try:
        os.makedirs(d)
    except OSError:
        if not os.path.isdir(d):
            raise
    return d


def fetch_package(url, pkg_type, pkg_name, downloads_dir):
    """
    Download the package at `url` in `download_dir` and return its filename.
    """
    import cgi
    import socket
    import requests
    from requests.exceptions import RequestException

    MAX_RETRIES = 3
    success = False

    for i in range(MAX_RETRIES):
        try:
            response = requests.get(url, timeout=20)
            print('response.status_code:', response.status_code,)
            if response.status_code == 200:
                success = True
                break
            else:
                import time
                time.sleep(1)
        except (RequestException, socket.timeout) as e:
            raise e

    if not success:
        raise Exception('Could not download content ({MAX_RETRIES} retries).'.format(**locals()))

    content_type = response.headers.get('content-type', '').lower()

    content_disposition = response.headers.get('content-disposition', '')
    value, params = cgi.parse_header(content_disposition)
    filename = params.get('filename') or url.split('/')[-1]

    # hack to get nuget packages to extract correctly
    if pkg_type == 'nuget':
        filename = pkg_name + '.nupkg'

    with open(os.path.join(downloads_dir, filename), 'wb') as out:
        out.write(response.content)
    return filename


def extract(archive_loc):
    call(' '.join([
        'extractcode',
        str(archive_loc)
        ]),
        shell=True
    )


def scan(extracted_archive_loc, json_scan_loc, csv_scan_loc):
    call(' '.join([
        'scancode',
        '--copyright',
        '--license',
        '--license-text',
        '--license-diag',
        '--info',
        '--classify',
        '--license-clarity-score',
        '--summary',
        '--summary-key-files',
         '-n', '4',
        '--json-pp', json_scan_loc,
        '--csv', csv_scan_loc,
         extracted_archive_loc
         ]),
        shell=True
    )


def get_packages(csv_loc='clearlylicensed.csv'):
    """
    Read the CSV at csv_loc and yield ordered mapping from package data
    """
    with open(csv_loc, 'rb') as csvfile:
        reader = csv.DictReader(csvfile)
        empty_template_row = OrderedDict((f, None) for f in reader.fieldnames)

        for row in reader:
            item = OrderedDict(empty_template_row)
            item.update(row)
            yield item


def process(input_csv='clearlylicensed.csv', output_csv='clearlylicensed-out.csv'):
    downloads_dir = create_dir('packages')
    scan_results_dir = create_dir('scans')

    # hardcode headers to keep order
    headers = 'download_url type namespace name version qualifier provider'.split()

    # list of mappings
    results = []

    for package in get_packages(csv_loc=input_csv):
        download_url = package.get('download_url')
        pkg_type = package.get('type')
        pkg_name = package.get('name')
        print('===========================================================')
        print('* Processing:', download_url)

        try:
            filename = fetch_package(download_url, pkg_type, pkg_name, downloads_dir)
        except Exception:
            package['scan_results_file'] = 'FAILED DOWNLOAD URL'
            results.append(package)
            continue

        archive_loc = os.path.join(downloads_dir, filename)
        json_scan_loc = os.path.join(scan_results_dir, filename + '-clarity.json')
        csv_scan_loc = os.path.join(scan_results_dir, filename + '-clarity.csv')
        extracted_archive_loc = archive_loc + '-extract'

        extract(archive_loc)
        scan(extracted_archive_loc, json_scan_loc, csv_scan_loc)

        scan_result = json.loads(
            open(json_scan_loc).read(),
            object_pairs_hook=OrderedDict
        )

        license_score = scan_result.get('license_score')
        package.update(license_score)
        package['scan_results_file'] = json_scan_loc
        results.append(package)

    headers = results[0].keys()
    with open(output_csv, 'wb') as outfile:
        dict_writer = csv.DictWriter(outfile, headers)
        dict_writer.writeheader()
        dict_writer.writerows(results)


if __name__ == '__main__':
    process()
