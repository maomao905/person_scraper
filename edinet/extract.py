import requests
import json
import os, io
import shutil
from zipfile import ZipFile
from pathlib import Path
from parser import XbrlParser, EXTRACT_KEYS
import shutil
from time import sleep

import util

def request(url):
    if url == '':
        return ''
    res = requests.get(url)
    res.encoding = res.apparent_encoding
    return res.text

def extract_from_sources(sources, output_path):
    results = []
    for source_id, source in sources.items():
        print('processing:' + source_id + source['title'])
        _results = extract_executive_names(source['link_executives'], source['link_profile'])
        if len(_results) == 0:
            print('No executive name found:', source['title'])
        else:
            results.extend(_results)
        sleep(0.5)
    save(results, output_path)

def extract_executive_names(link_executives, link_profile):
    html_executives = request(link_executives)
    html_profile = request(link_profile)
    xp = XbrlParser(html_executives, html_profile)
    return xp.parse_xbrl()

def save(results, output_path):
    import csv
    file_exists = Path(output_path).exists()
    with open(output_path, 'a', encoding='utf-8') as f:
        resultCsvWriter = csv.DictWriter(f, EXTRACT_KEYS, lineterminator='\n')
        if not file_exists:
            resultCsvWriter.writeheader()
        resultCsvWriter.writerows(results)

def extract(sources_dir, output_path):
    DONE_SOURCES = os.path.join(sources_dir, 'done/')
    util.mkdir(DONE_SOURCES)

    for file_name in Path(sources_dir).glob('*.json'):
        print(str(file_name) + ' loading...')
        with open(file_name, 'r') as f:
            sources = json.load(f)

        extract_from_sources(sources, output_path)
        shutil.move(str(file_name), DONE_SOURCES)

if __name__=='__main__':
    TEST_MODE = False
    if TEST_MODE:
        from pprint import pprint
        link_profile = 'http://resource.ufocatch.com/xbrl/edinet/ED2019090900115/S100GX4X/XBRL/PublicDoc/0000000_header_jpcrp030000-asr-001_E00890-000_2019-05-31_02_2019-09-09_ixbrl.htm'
        link_executives = 'http://resource.ufocatch.com/xbrl/edinet/ED2019090900115/S100GX4X/XBRL/PublicDoc/0104010_honbun_jpcrp030000-asr-001_E00890-000_2019-05-31_02_2019-09-09_ixbrl.htm'
        results = extract_executive_names(link_executives, link_profile)
        pprint(results)
    else:
        import argparse
        parser = argparse.ArgumentParser()
        parser.add_argument(
            '--sources-dir',
            '-s',
            required=True,
            help='Sources directory',
        )
        parser.add_argument(
            '--output-path',
            '-o',
            required=True,
            help='Output csv file path that it saves name data to'
        )
        args = parser.parse_args()
        extract(args.sources_dir, args.output_path)
