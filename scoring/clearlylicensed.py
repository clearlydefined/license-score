
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division

import cgi
from collections import Counter
from collections import namedtuple
from collections import OrderedDict
import csv

try:
    from itertools import imap
except:
    imap = map

import json
import os
from os import path
from subprocess import call
import traceback

try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse

import attr  # NOQA
import requests
from scancode.pool import get_pool


current_dir = path.abspath(path.dirname(__file__))

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
    `output_csv` with details data and another CSV at `aggregates_csv` with
    aggreated data.

    The `input_csv` must contain these columns: download_url, filename and
    package URL fields (type, namespace, name, version).

    If `do_fetch` is True, fetch the Packages. Otherwise, assume Packages files
    are in the "packages" directory.

    If `do_extract` is True, extract the downloaded package archives. Otherwise,
    assume archives are already extracted in the "extracts" directory.

    If `do_scan` is True, scan the Packages. Otherwise, assume Packages scan
    files are in the "scans" directory.

    If `do_rescore` is True, re-process the Packages to recompute the score in
    the "scans" directory.

    """
    downloads_dir = create_dir('downloads', base_dir=base_dir)
    extracts_dir = create_dir('extracts', base_dir=base_dir)
    scans_dir = create_dir('scans', base_dir=base_dir)

    packages_data = list(get_packages_data(csv_loc=input_csv))

    ############################################################################
    # uncomment for testing on a smaller subset
#     import random
#     random.shuffle(packages_data)
#     packages_data = packages_data[:4]
    ############################################################################

    if types:
        packages_data = [p for p in packages_data if p.get('type') in types]

    ############################################################################
    # fetch
    ############################################################################
    if do_fetch or do_extract:
        for i, package in enumerate(packages_data):
            pkg_type = package.get('type')
            download_url = package.get('download_url')
            pkg_name = package.get('name')
            print('===========================================================')
            print(i, 'Fetching/extracting: ', download_url)

            archive_filename = package.get('filename')
            downloaded_archive_loc = path.join(downloads_dir, pkg_type, archive_filename)
            archive_extract_dir = archive_filename + '-extract'
            extracted_archive_loc = path.join(downloads_dir, pkg_type, archive_extract_dir)
            target_extracted_archive_loc = path.join(extracts_dir, pkg_type, archive_extract_dir)

            if do_fetch:
                fetch_file = do_fetch
                # filename MUST be present in CSV, otherwise the packages are fetched
                if archive_filename:
                    if not path.exists(downloaded_archive_loc):
                        fetch_file = True
                else:
                    fetch_file = True

                if fetch_file:
                    try:
                        archive_filename = fetch_package(download_url, pkg_type, pkg_name, downloads_dir)
                    except Exception:
                        # package['scan_results_file'] = 'FAILED DOWNLOAD URL:\n{}'.traceback.format_exc()
                        # results.append(package)
                        continue

            if not path.exists(downloaded_archive_loc):
                # things did not download alright
                continue

            if do_extract:
                extract(downloaded_archive_loc)
            # move the extracts to an extract dir
            if path.exists(extracted_archive_loc):
                os.rename(extracted_archive_loc, target_extracted_archive_loc)

    ############################################################################
    # scan
    ############################################################################
    if do_scan:
        scan_kwargs = []
        for package in packages_data:
            jsl = get_json_scan_loc(package, scans_dir)
            eal = get_extracted_archive_loc(package, extracts_dir)
            if path.exists(eal) and not path.exists(jsl):
                scan_kwargs.append(get_initial_scan_kwargs(eal, jsl))
        run_scans(scan_kwargs, processes=10)


    ############################################################################
    # rescore
    ############################################################################
    if do_rescore:
        rescore_kwargs = []
        for package in packages_data:
            jsl = get_json_scan_loc(package, scans_dir)
            print('rescore: {}'.format(jsl))
            if path.exists(jsl):
                rescore_kwargs.append(get_recompute_score_kwargs(jsl))
        run_scans(rescore_kwargs, processes=10)

    ############################################################################
    # Load JSON scan results, save details
    ############################################################################
    # list of mappings, one per package of {
    results = []

    for i, package in enumerate(packages_data):
        pkg_type = package.get('type')
        download_url = package.get('download_url')
        print(i, 'Loading scan for: ', download_url)
        json_scan_loc = get_json_scan_loc(package, scans_dir)
        if not path.exists(json_scan_loc):
            continue
        lscore = get_license_score(json_scan_loc)
        package.update(lscore)
        results.append(package)

    headers = results[0].keys()
    with open(output_csv, 'wb') as outfile:
        dict_writer = csv.DictWriter(outfile, headers)
        dict_writer.writeheader()
        dict_writer.writerows(results)

    ############################################################################
    # compute and save aggregates
    ############################################################################

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


def get_json_scan_loc(package, scans_dir):
    """
    Return a JSON scan file location given a package mapping.
    """
    return path.join(
        scans_dir,
        package.get('type'),
        package.get('filename') + '-clarity.json'
    )


def get_extracted_archive_loc(package, extracts_dir):
        return path.join(
            extracts_dir,
            package.get('type'),
            package.get('filename') + '-extract'
        )


def get_license_score(json_scan_loc):
    """
    Return the clarity score data from a single package JSON scan file location.
    """
    if not path.exists(json_scan_loc):
        return {}

    with open(json_scan_loc, 'rb') as scanned:
        scan_result = json.load(scanned, object_pairs_hook=OrderedDict)

    license_score = scan_result['license_clarity_score'] or {}
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

    return license_score


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

    @classmethod
    def sum(cls, label, aggregates):
        """
        Return a new aggregate summing a list of aggregates.
        """
        agg = Aggregate(label)
        for a in aggregates:
            agg.gem += a.gem
            agg.maven += a.maven
            agg.npm += a.npm
            agg.nuget += a.nuget
            agg.pypi += a.pypi
            agg.total += a.total
        return agg


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
                pcounts = package_counts[a]
                if pcounts:
                    setattr(tally, a, round(value / pcounts, 1))
            tally.label = 'score average'

        if tally.label == 'discovered':
            # compute a ratio between 0 and 100
            for a in Aggregate.ptypes:
                value = getattr(tally, a)
                pcounts = package_counts[a]
                if pcounts:
                    setattr(tally, a, round((value / pcounts) * 100, 1))
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
                pcounts = package_counts[a]
                if pcounts:
                    setattr(percent, a, round((value / pcounts) * 100, 1))
            percent.label = 'percentage with {}'.format(percent.label)

        if percent.label == 'score':
            # compute a ratio between 0 and 100
            for a in Aggregate.ptypes:
                value = getattr(percent, a)
                pcounts = package_counts[a]
                if pcounts:
                    setattr(percent, a, round(value / pcounts, 1))
            percent.label = 'score average'

        if percent.label == 'discovered':
            # compute a ratio between 0 and 100
            for a in Aggregate.ptypes:
                value = getattr(percent, a)
                pcounts = package_counts[a]
                if pcounts:
                    setattr(percent, a, round((value / pcounts) * 100, 1))
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
    aggregate_name = 'Table 4. Number of packages over a score by type'
    ############################################################################
    brackets_thresholds = []
    for bk in (40, 50, 60, 70, 80):
        aggs = [_agg for _bk, _agg in brackets.items() if _bk >= bk]
        brackets_thresholds.append(Aggregate.sum('over {}'.format(bk), aggs))
    aggregate_tables[aggregate_name] = brackets_thresholds

    ############################################################################
    aggregate_name = 'Table 5. Number of packages by percentage of discovered license brackets and by type'
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
    # aggregate_name= 'Table 6. Number of packages by type above a license score threshold'
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
        print('Response.status_code:', response.status_code,)
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

    filepath = path.join(download_dir, filename)

    with open(filepath, 'wb') as out:
        out.write(response.content)
    return filename


def extract(archive_loc):
    call(' '.join(['extractcode', str(archive_loc)]), shell=True)


def extract_shallow(archive_loc):
    call(' '.join(['extractcode', '--shallow', str(archive_loc)]), shell=True)


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
    d = path.join(base_dir, name)
    try:
        os.makedirs(d)
    except OSError:
        if not os.path.isdir(d):
            raise
    return d


def echo_func(*args, **kwargs):
    print (*args)


def get_initial_scan_kwargs(extracted_archive_loc, json_scan_loc):

        return dict(
            input=extracted_archive_loc,
            output_json_pp=json_scan_loc,
            package=True,
            copyright=True,
            license=True,
            license_diag=True,
            info=True,
            classify=True,
            license_clarity_score=True,
            processes=0,
            timeout=10,

            max_in_memory=0,
            return_results=False,

            # quiet=False,
            # verbose=True,
            # echo_func=echo_func,
        )


def get_recompute_score_kwargs(json_scan_loc):

        return dict(
            input=json_scan_loc,
            from_json=True,
            output_json_pp=json_scan_loc,
            classify=True,
            license_clarity_score=True,
            max_in_memory=0,
            return_results=False,
            # quiet=False,
            # verbose=True,
            # echo_func=echo_func,
        )


def run_scan(scan_kwargs):
    from scancode import cli
    print('Running scan for: {}'.format(scan_kwargs.get('input', '')))
    success, _results = cli.run_scan(**scan_kwargs)
    return success


def run_scans(scan_kwargs, processes=1):
    """
    Run a scan with the scancode.cli.run_scan function using the `scan_kwargs`
    mapping of keyword arguments across `processes` processes.
    """
    success = True
    pool = None
    scans = None
    completed = 0
    try:
        if processes >= 1:
            pool = get_pool(processes=processes, maxtasksperchild=10000)
            scans = pool.imap_unordered(run_scan, scan_kwargs, chunksize=1)
            pool.close()
        else:
            scans = imap(run_scan, scan_kwargs)

        while True:
            try:
                _scan_success = scans.next()
                completed += 1
                print(completed)
            except StopIteration:
                break
            except KeyboardInterrupt:
                success = False
                if pool:
                    pool.terminate()
                break
    finally:
        if pool:
            # ensure the pool is really dead to work around a Python 2.7.3 bug:
            # http://bugs.python.org/issue15101
            pool.terminate()
    return success


if __name__ == '__main__':

    # set to True to execute/re-execute this step
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
