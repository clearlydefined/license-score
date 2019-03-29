
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division


import cgi
from collections import namedtuple
from collections import OrderedDict
import csv
import json
import os
from subprocess import call
import traceback
from collections import Counter

try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse

import attr  # NOQA
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


brackets_labels = OrderedDict([
    (0, '0'),
    (1, '1 to 9'),
    (10, '10 to 19'),
    (20, '20 to 29'),
    (30, '30 to 39'),
    (40, '40 to 49'),
    (50, '50 to 59'),
    (60, '60 to 69'),
    (70, '70 to 79'),
    (80, '80 to 89'),
    (90, '90 to 99'),
    (100, '100'),
])


def compute_license_score(
        input_csv='5000-packages-license-score-data.csv',
        output_csv='5000-packages-license-score-results-out.csv',
        aggregates_csv='5000-packages-license-score-results-aggregates.csv',
        base_dir=current_dir,
        do_fetch=True,
        do_extract=True,
        do_scan=True,
        do_rescore=True,
        types=()):
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

    package_data = get_packages_data(csv_loc=input_csv)

    # uncomment for testing on a smaller subset
    #     package_data = list(package_data)
    #     import random
    #     random.shuffle(package_data)
    #     package_data = package_data[:30]

    for i, package in enumerate(package_data):
        pkg_type = package.get('type')
        if types and pkg_type not in types:
            continue
        download_url = package.get('download_url')
        pkg_name = package.get('name')
        print('===========================================================')
        print(i, 'Processing: ', download_url)

        archive_filename = package.get('filename')
        downloaded_archive_loc = os.path.join(downloads_dir, pkg_type, archive_filename)
        archive_extract_dir = archive_filename + '-extract'
        extracted_archive_loc = os.path.join(downloads_dir, pkg_type, archive_extract_dir)
        target_extracted_archive_loc = os.path.join(extracts_dir, pkg_type, archive_extract_dir)

        if do_fetch:
            fetch_file = do_fetch
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

        json_scan_loc = os.path.join(scans_dir, pkg_type, archive_filename + '-clarity.json')
        csv_scan_loc = os.path.join(scans_dir, pkg_type, archive_filename + '-clarity.csv')

        if do_rescore and os.path.exists(json_scan_loc) and not do_scan:
            try:
                recompute_score(json_scan_loc, csv_scan_loc)
            except KeyboardInterrupt:
                break
            except Exception:
                pass

        if do_scan and not os.path.exists(json_scan_loc):
            try:
                scan(target_extracted_archive_loc, json_scan_loc, csv_scan_loc)
            except KeyboardInterrupt:
                break
            except Exception:
                pass

        scan_result = {}
        if os.path.exists(json_scan_loc):
            with open(json_scan_loc, 'rb') as scanned:
                scan_result = json.load(scanned, object_pairs_hook=OrderedDict)

        license_score = scan_result.get('license_clarity_score', {})
        if license_score:
            renamed = 'score', 'declared', 'discovered', 'consistency', 'spdx', 'full_text'
            kvs = zip(renamed, license_score.values())
            license_score = OrderedDict(kvs)

            # convert booleans to 0/1
            decl = license_score['declared']
            license_score['declared'] = 1 if decl else 0
            cons = license_score['consistency']
            license_score['consistency'] = 1 if cons else 0
            spdx = license_score['spdx']
            license_score['spdx'] = 1 if spdx else 0
            full_text = license_score['full_text']
            license_score['full_text'] = 1 if full_text else 0

            # compute brackets
            score = int(license_score['score'])
            score_bracket = int(round(score / 10, 1)) * 10
            if score_bracket == 0:
                if score != 0:
                    score_bracket = 1
            license_score['score_bracket'] = score_bracket

            # compute brackets
            disco = float(license_score['discovered'])
            discovered_bracket = int(round(disco * 10, 1)) * 10
            if discovered_bracket == 0:
                if disco != 0:
                    discovered_bracket = 1
            license_score['discovered_bracket'] = discovered_bracket

            package.update(license_score)

        results.append(package)

    headers = results[0].keys()
    with open(output_csv, 'wb') as outfile:
        dict_writer = csv.DictWriter(outfile, headers)
        dict_writer.writeheader()
        dict_writer.writerows(results)

    aggregate_tables = compute_aggregates(results)

    with open(aggregates_csv, 'wb') as aggfile:
        for name, aggregate_table in aggregate_tables.items():
            aggfile.write(name + '\n')
            aggregated = [
                attr.asdict(aggregate, dict_factory=OrderedDict)
                for aggregate in aggregate_table]

            headers = aggregated[0].keys()
            dict_writer = csv.DictWriter(aggfile, headers)
            dict_writer.writeheader()
            dict_writer.writerows(aggregated)
            aggfile.write('\n\n')


_dp_fields = [
    'type',
    'score', 'declared', 'discovered', 'consistency', 'spdx', 'full_text',
    'score_bracket', 'discovered_bracket']

dp_fields = set(_dp_fields)
Datapoint = namedtuple('Datapoint', _dp_fields)


@attr.s(slots=True)
class Aggregate(object):
    label = attr.ib()
    gem = attr.ib(default=0)
    maven = attr.ib(default=0)
    npm = attr.ib(default=0)
    nuget = attr.ib(default=0)
    pypi = attr.ib(default=0)
    total = attr.ib(default=0)

    ptypes = 'gem', 'maven', 'npm', 'nuget', 'pypi', 'total',

    def compute_total(self):
        self.total = (self.gem + self.maven + self.nuget + self.npm + self.pypi)


def compute_median(datapoints):
    """
    Return a median score Aggregate
    """
    median = Aggregate('score median')

    # make each package type a list attribute that we will use to compute the median
    for a in Aggregate.ptypes:
        setattr(median, a, list())

    # accumulate values
    for datapoint in datapoints:
        di = getattr(median, datapoint.type)
        di.append(datapoint.score)
        di = getattr(median, 'total')
        di.append(datapoint.score)

    import statistics  # NOQA
    for a in Aggregate.ptypes:
        dl = getattr(median, a)
        med = dl and statistics.median(dl) or 0
        setattr(median, a, med)

    return median


def compute_aggregates(results):
    """
    Return a mapping of aggregates as {name: data} where the data for an
    aggregate is a list of Aggregate objects.
    {'Table 1. Totals by type':
        [
            Aggregate(label='score',gem=12, maven=23,...),
            Aggregate(label='discovered',gem=12, maven=23,...),
            Aggregate(label='score',gem=12, maven=23,...),
        ],
     'Table 2. Lorem ipsum...':
        ...
    }
    """
    datapoints = []
    for package in results:
        datapoint = Datapoint(**{k: v for k, v in package.items() if k in dp_fields})
        datapoints.append(datapoint)

    aggregate_tables = OrderedDict()

    ############################################################################
    aggregate_name = 'Table.1 Tallies for the score and each scoring element by package type'
    ############################################################################
    tallies = OrderedDict()
    package_counts = Counter()
    def update_count(_label, _tallies, _datapoint):
        _tally = _tallies.get(_label)
        if _tally is None:
            _tally = Aggregate(label=_label)
            _tallies[_label] = _tally
        _value = getattr(_tally, _datapoint.type) + getattr(_datapoint, _label, 0)
        setattr(_tally, _datapoint.type, _value)

    for datapoint in datapoints:
        package_counts[datapoint.type] += 1
        for label in ('score', 'declared', 'discovered', 'consistency', 'spdx', 'full_text',):
            update_count(label, tallies, datapoint)

    # we prefix with median and suffix with counts
    median = compute_median(datapoints)
    aggregate_tables[aggregate_name] = [median] + list(tallies.values())

    # append package counts
    package_counts['total'] = sum(package_counts.values())
    package_counts_aggregate = Aggregate('package_counts', **package_counts)
    aggregate_tables[aggregate_name].append(package_counts_aggregate)

    # update totals
    for tally in  tallies.values():
        tally.compute_total()
        if tally.label == 'score':
            # compute a ratio between 0 and 100
            for a in Aggregate.ptypes:
                value = getattr(tally, a)
                setattr(tally, a, round(value / package_counts[a], 1))
            tally.label = 'score average'

        if tally.label == 'discovered':
            # compute a ratio between 0 and 100
            for a in Aggregate.ptypes:
                value = getattr(tally, a)
                setattr(tally, a, round((value / package_counts[a]) * 100, 1))
            tally.label = 'discovered average'


    ############################################################################
    aggregate_name = 'Table 2. Scoring elements percentage by package type'
    ############################################################################
    percentages = OrderedDict()
    for datapoint in datapoints:
        for label in ('score', 'declared', 'discovered', 'consistency', 'spdx', 'full_text',):
            update_count(label, percentages, datapoint)

    aggregate_tables[aggregate_name] = percentages.values()

    # compute total and averages for discrete values
    for percent in percentages.values():
        percent.compute_total()
        if percent.label not in ('score', 'discovered',):
            # compute a ratio between 0 and 100
            for a in Aggregate.ptypes:
                value = getattr(percent, a)
                setattr(percent, a, round((value / package_counts[a]) * 100, 1))
            percent.label = 'percentage with {}'.format(percent.label)

        if percent.label == 'score':
            # compute a ratio between 0 and 100
            for a in Aggregate.ptypes:
                value = getattr(percent, a)
                setattr(percent, a, round(value / package_counts[a], 1))
            percent.label = 'score average'

        if percent.label == 'discovered':
            # compute a ratio between 0 and 100
            for a in Aggregate.ptypes:
                value = getattr(percent, a)
                setattr(percent, a, round((value / package_counts[a]) * 100, 1))
            percent.label = 'discovered average'


    ############################################################################
    aggregate_name = 'Table 3. Number of packages by license score brackets and by type'
    ############################################################################
    brackets = OrderedDict([
        (bk, Aggregate(label=blabel)) for bk, blabel in brackets_labels.items()
    ])

    def update_bracket(_bracket_key, _brackets, _datapoint_type):
        _bracket = _brackets.get(_bracket_key)
        _value = getattr(_bracket, _datapoint_type) + 1
        setattr(_bracket, _datapoint_type, _value)

    for datapoint in datapoints:
        update_bracket(datapoint.score_bracket, brackets, datapoint.type)

    # update totals
    for bracket in brackets.values():
        bracket.compute_total()

    aggregate_tables[aggregate_name] = brackets.values()
    aggregate_tables[aggregate_name].append(package_counts_aggregate)


    ############################################################################
    aggregate_name = 'Table 4. Number of packages by percentage of discovered license brackets and by type'
    ############################################################################
    brackets = OrderedDict([
        (bk, Aggregate(label=blabel)) for bk, blabel in brackets_labels.items()
    ])

    for datapoint in datapoints:
        update_bracket(datapoint.discovered_bracket, brackets, datapoint.type)

    # update totals
    for bracket in  brackets.values():
        bracket.compute_total()

    aggregate_tables[aggregate_name] = brackets.values()
    aggregate_tables[aggregate_name].append(package_counts_aggregate)


    ############################################################################
    # aggregate_name= 'Table 4. Number of packages by type above a license score threshold'
    ############################################################################

    return aggregate_tables


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
        '--package',
        '--copyright',
        '--license',
        '--license-text',
        '--license-diag',
        '--info',
         '-n', '3',
        '--json-pp', json_scan_loc,
        '--csv', csv_scan_loc,

        '--timeout', '10',
        '--max-in-memory', '0',

        '--classify',
        '--license-clarity-score',

         extracted_archive_loc
         ]),
        shell=True
    )


def recompute_score(json_scan_loc, csv_scan_loc):
    call(' '.join([
        'scancode',
        '--from-json',
        json_scan_loc,

        '--json-pp', json_scan_loc,
        '--csv', csv_scan_loc,

        '--classify',
        '--license-clarity-score',

        '--max-in-memory', '0',
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

    do_fetch = False
    do_extract = False
    do_scan = False
    do_rescore = False

    # directory where the downloads are fetched, extracted and scanned
    base_dir = os.environ.get('CLEARDATA', current_dir)

    compute_license_score(
        base_dir=base_dir,
        do_fetch=do_fetch,
        do_extract=do_extract,
        do_scan=do_scan,
        do_rescore=do_rescore,
        types=set([
            'gem',
            'maven',
            'nuget',
            'npm',
            'pypi',
        ]),
    )
