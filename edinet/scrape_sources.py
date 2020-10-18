import requests
import xml.etree.ElementTree as ET
import json
import os
import io
import re
from collections import defaultdict
from datetime import datetime as dt
from time import sleep

import util

INDICATOR_PROFILE_LINK   = '0000000_header'
INDICATOR_EXECUTIVE_LINK = '0104010'

def request(base_url, page):
    url = os.path.join(base_url, str(page))
    res = requests.get(url)
    return res.text

def is_yuho(title):
    return '有価証券報告書' in title

def valid_time(updated, since):
    updated_time = dt.strptime(updated, '%Y-%m-%dT%H:%M:%S+09:00')
    return updated_time >= since

def save(file_path, sources):
    with open(file_path, 'w') as f:
        json.dump(sources, f, ensure_ascii=False, indent=4)

def get_person_related_links(el, namespace):
    """
    There are patterns in the link that indicates it contains executive names or company profile.
    """
    link_profile = ''
    link_executives     = ''
    for link_el in el.findall(f'./{namespace}link[@type="text/html"]'):
        if link_el.attrib is None:
            continue
        if 'href' not in link_el.attrib:
            continue
        link = link_el.attrib['href']
        if INDICATOR_PROFILE_LINK in link:
            link_profile = link
        elif INDICATOR_EXECUTIVE_LINK in link:
            link_executives = link
    return link_profile, link_executives

def get_sources(tree, namespace, since):
    sources = {}
    for el in tree.findall(f'.//{namespace}entry'):
        updated_at = el.find(namespace+'updated').text
        if not valid_time(updated_at, since):
            return sources, True

        title = el.find(namespace+'title').text
        title = str(title)
        if not is_yuho(title):
            continue

        link_profile, link_executives = get_person_related_links(el, namespace)
        if all(link == '' for link in (link_profile, link_executives)):
            print(f'{title} has no person related link')
            continue

        source_id = el.find(namespace+'id').text

        sources[source_id] = {
            'title':               title,
            'link_profile':        link_profile,
            'link_executives':     link_executives,
            'updated_at':          updated_at,
        }
    return sources, False

def scrape_sources(since, output_dir):
    base_url = 'http://resource.ufocatch.com/atom/edinetx/'
    namespace = '{http://www.w3.org/2005/Atom}'
    page = 1
    total_count = 0

    util.mkdir(output_dir)

    while True:
        response_string = request(base_url, page)
        ET_tree = ET.fromstring(response_string)
        ET.register_namespace('', namespace[1:-1])

        sources, done = get_sources(ET_tree, namespace, since)
        total_count += len(sources)
        if len(sources) > 0:
            out_file_path = f'{output_dir}/source_{page}.json'
            save(out_file_path, sources)

        if done:
            print(f'Done!')
            break
        print(f'processed {page}th page [total: {total_count} sources]')
        page += 1
        sleep(0.5)

if __name__=='__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--since',
        '-s',
        required=True,
        help='Since when you scrape edinet data (format: %Y-%m-%d)',
    )
    parser.add_argument(
        '--output-dir',
        '-o',
        required=True,
        help='Directory in which you save data'
    )
    args = parser.parse_args()

    since = dt.strptime(args.since,'%Y-%m-%d')
    scrape_sources(since, args.output_dir)
