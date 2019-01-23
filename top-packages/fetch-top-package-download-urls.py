from __future__ import print_function

from collections import OrderedDict
import csv
import itertools
import json
import os


def get_maven_packages(filename):
    with open(filename, 'rb') as csvfile:
        reader = csv.DictReader(csvfile)
        empty_template_row = OrderedDict((f, None) for f in reader.fieldnames)

        for row in reader:
            item = OrderedDict(empty_template_row)
            item.update(row)
            yield item


def maven_latest_release(group_id, artifact_id):
    """
    From the given group_id, artifact_id gather the latest release version from Maven
    central.
    """
    import xml.etree.ElementTree as ET
    import requests

    base_url = 'http://central.maven.org/maven2/'
    metadata_url = base_url + '{}/{}/maven-metadata.xml'.format(group_id, artifact_id)

    response = requests.get(metadata_url)

    if response.status_code == 200:
        for item in ET.fromstring(response.text).iter():
            if item.tag == 'latest':
                return item.text


def maven_source_url(group_id, artifact_id, version):
    base_url = 'http://central.maven.org/maven2/'
    grp_art_ver_url = base_url + '{}/{}/{}/'.format(group_id, artifact_id, version)
    return grp_art_ver_url + '{}-{}-sources.jar'.format(artifact_id, version)


def process_maven():
    print('Querying Maven central for latest package versions...')
    for mvn_package in get_maven_packages('./source-data/mvn1.5k.csv'):
        group_id = mvn_package.get('group_id')
        group_id_url = '/'.join(group_id.split('.'))

        artifact_id = mvn_package.get('artifact_id')
        git_url = mvn_package.get('git_url')

        latest_version = maven_latest_release(group_id_url, artifact_id)
        if not latest_version:
            continue

        download_url = maven_source_url(group_id_url, artifact_id, latest_version)
        qualifier = 'classifier=sources'

        yield OrderedDict([
            ('download_url', download_url),
            ('type', 'maven'),
            ('namespace', group_id),
            ('name', artifact_id),
            ('version', latest_version),
            ('qualifier', qualifier),
            ('provider', 'mavencentral'),
        ])


def get_pypi_packages(filename):
    with open(filename) as jsonfile:
        data = json.load(jsonfile)
        for row in data['rows']:
            yield row


def pypi_latest_release(name):
    import requests
    
    pypi_url = 'https://pypi.org/pypi/{}/json'.format(name)
    
    response = requests.get(pypi_url)

    if response.status_code == 200:
        data = response.json()
        return data.get('info').get('version')


def pypi_source_url(name, version):
    import requests

    pypi_url = 'https://pypi.org/pypi/{}/{}/json'.format(name, version)
    
    response = requests.get(pypi_url)

    if response.status_code == 200:
        data = response.json()
        for url in data.get('urls', []):
            if url.get('packagetype') == 'sdist':
                return url.get('url')


def process_pypi():
    print('Querying PyPI for latest package version and source URLs...')
    for pypi_package in get_pypi_packages('./source-data/top-pypi-packages-365-days.json'):
        name = pypi_package.get('project')
        latest_version = pypi_latest_release(name)

        download_url = pypi_source_url(name, latest_version)
        if not download_url:
            continue

        yield OrderedDict([
            ('download_url', download_url),
            ('type', 'pypi'),
            ('name', name),
            ('version', latest_version),
            ('provider', 'pypi')
        ])


def get_top_nuget_packages():
    import requests

    base_url = 'https://api-v2v3search-0.nuget.org/query?prerelease=false&take=1000'

    api_data = []

    # Grab 30000 packages, with 1000 per request
    print('Querying NuGet API for package metadata...')
    for i in range(30):
        if i == 0:
            response = requests.get(base_url)
        else: 
            response = requests.get(base_url + '&skip={}'.format(i * 1000))

        if response.status_code == 200:
            api_data.extend(response.json().get('data'))

    print('Sorting package by popularity...')
    from operator import itemgetter
    return sorted(api_data, key=itemgetter('totalDownloads'))


def process_nuget():
    for nuget_package in get_top_nuget_packages():
        name, version = nuget_package.get('id'), nuget_package.get('version')
        download_url = 'https://www.nuget.org/api/v2/package/{}/{}'.format(name, version)
        yield OrderedDict([
          ('download_url', download_url),
          ('type', 'nuget'),
          ('name', name),
          ('version', version),
          ('provider', 'nuget'),
        ])


def get_top_npm_packages(filename):
    with open(filename, 'rb') as csvfile:
        reader = csv.DictReader(csvfile)
        empty_template_row = OrderedDict((f, None) for f in reader.fieldnames)

        for row in reader:
            item = OrderedDict(empty_template_row)
            item.update(row)
            yield item


def npm_latest_release(name):
    url = 'https://replicate.npmjs.com/{}'.format(name)
    
    import requests
    response = requests.get(url)
    if response.status_code == 200:
        return response.json().get('dist-tags').get('latest')


def process_npm():
    print('Querying NPM registry for latest package versions...')
    for npm_package in get_top_npm_packages('./source-data/npm-pagerank.csv'):
        name = npm_package.get('name')
        latest_version = npm_latest_release(name)
        if not latest_version:
            continue
        
        download_url = 'https://registry.npmjs.org/{name}/-/{name}-{version}.tgz'.format(name=name, version=latest_version)

        yield OrderedDict([
            ('download_url', download_url),
            ('type', 'npm'),
            ('name', name),
            ('version', latest_version),
            ('provider', 'npmjs'),
        ])


def parse_gem_names(text):
    from bs4 import BeautifulSoup
    parsed_html = BeautifulSoup(text, 'lxml')

    return [div.h3.text for div in parsed_html.findAll('div', {'class': 'stats__graph__gem'})]


def top_downloaded_gem_names():
    import requests

    top_gem_names = []
    
    for page_num in range(1, 101):
        url = 'https://rubygems.org/stats?page={}'.format(page_num)

        response = requests.get(url)
        if response.status_code == 200:
            top_gem_names.extend(parse_gem_names(response.text))
    
    return top_gem_names


def process_rubygems():
    print("Querying rubygems.org/stats for a list of most popular packages...")
    gem_names = top_downloaded_gem_names()

    print("Querying rubygems API for latest version of popular packages...")
    for gem_name in gem_names:
        import requests

        url = 'https://rubygems.org/api/v1/gems/{}.json'.format(gem_name)

        response = requests.get(url)
        if response.status_code == 200:
            name = gem_name
            version = response.json().get('version')

            download_url = response.json().get('gem_uri')
            if not download_url:
                continue

            yield OrderedDict([
                ('download_url', download_url),
                ('type', 'gem'),
                ('name', name),
                ('version', version),
                ('provider', 'rubygems'),
            ])


def process():
    headers = 'download_url type namespace name version qualifier provider'.split()
    process_pypi()
    with open('./top-packages-out.csv', 'wb') as outfile:
        dict_writer = csv.DictWriter(outfile, headers)
        dict_writer.writeheader()
        dict_writer.writerows(itertools.islice(process_maven(), 1000))
        dict_writer.writerows(itertools.islice(process_pypi(), 1000))
        dict_writer.writerows(itertools.islice(process_nuget(), 1000))
        dict_writer.writerows(itertools.islice(process_npm(), 1000))
        dict_writer.writerows(itertools.islice(process_rubygems(), 1000))


process()
