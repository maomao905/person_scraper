from xbrl import XBRLParser
import os, re, csv
from collections import defaultdict
import lxml.html

TAG_EXECUTIVE_BLOCK   = 'jpcrp_cor:informationaboutofficerstextblock'
TAG_POSITION_AND_NAME = 'TitleAndNameOfRepresentativeCoverPage'
TAG_FILER_NAME        = 'FilerNameInJapaneseDEI'

EXTRACT_KEYS = ['company_name', 'name', 'position',]

"""
ref: https://qiita.com/NaoyaOura/items/837fbf5d469da0438cc7
"""
class XbrlParser(XBRLParser):
    def __init__(self, html_executives, html_profile):
        self.html_executives = html_executives
        self.html_profile = html_profile

    def parse_xbrl(self):
        results = []
        sub_html = lxml.html.fromstring(self.html_profile.encode('utf-8'))
        company_names = sub_html.xpath(f'//nonnumeric[contains(@name, "{TAG_FILER_NAME}")]')
        company_name = company_names[0].text_content().strip() if len(company_names) > 0 else ''

        name_position_dict = {}
        if self.html_executives != '':
            name_position_dict = self.get_exective_names(self.html_executives)

        # try profile html to get representative name if it cannot extract executive.
        if len(name_position_dict) == 0:
            result = self.get_representative_name(sub_html)
            if result is None:
                print('Warn: no result from profile html')
                return results
            result['company_name'] = company_name
            results.append(result)
        else:
            for name, position in name_position_dict.items():
                results.append({
                    'company_name': company_name,
                    'name': name,
                    'position': position,
                })
        return results

    def get_representative_name(self, html):
        result = {}
        nodes = html.xpath(f'//nonnumeric[contains(@name, "{TAG_POSITION_AND_NAME}")]')
        if len(nodes) == 0:
            return None
        text = nodes[0].text_content().strip()
        words = text.split()
        if len(words) < 2:
            print('Warn: words lenth is not correct', words)
            return None
        elif len(words) == 2:
            result['position'] = words[0]
            result['name'] = words[1]
        else:
            result['position'] = words[0]
            result['name'] = ' '.join(words[1:])
        return result

    def is_executive_header_row(self, text):
        if '役職名' in text:
            return True
        if '氏名' in text:
            return True
        return False

    def _get_table_rows(self, table):
        return table.xpath('./tbody//tr') or table.xpath('.//tr')

    def get_exective_block_info(self, table):
        trs = self._get_table_rows(table)
        is_executive_block = False
        column_index_position = None
        column_index_name = None
        for tr in trs:
            for idx, td in enumerate(tr.xpath('./td')):
                text = td.text_content()
                if re.search(r'役名|役職名', text):
                    column_index_position = idx
                if re.search(r'氏名', text):
                    column_index_name = idx
            is_executive_block = all(idx is not None for idx in (column_index_name, column_index_position,))
            if is_executive_block:
                tr.drop_tree()
                return table, column_index_position, column_index_name

        return None, 0, 0

    def is_executive_row(self, row):
        column_length = len(list(row.iterchildren()))
        return column_length >= 5

    def get_exective_names(self, node_string):
        name_dict = {}
        html = lxml.html.fromstring(node_string.encode('utf-8'))
        executive_header_h3 = html.xpath('//h3[contains(., "役員の状況")]')
        executive_header_h4 = html.xpath('//h4[contains(., "役員の状況")]')
        executive_headers = executive_header_h3 + executive_header_h4
        if len(executive_headers) == 0:
            return name_dict
        if len(executive_headers) > 1:
            print('more than one executive_headers')
        executive_block = executive_headers[0].getparent()
        for table in executive_block.xpath('.//table'):
            executive_node, column_index_position, column_index_name = self.get_exective_block_info(table)
            if executive_node is None:
                continue

            trs = self._get_table_rows(executive_node)
            for tr in trs:
                if not self.is_executive_row(tr):
                    continue

                tds = tr.xpath('./td')
                position = tds[column_index_position].text_content().strip()
                position = re.sub('\s+', ' ', position)
                name = tds[column_index_name].text_content().strip()
                name = re.sub('\s+', ' ', name)
                if name == '' or position == '':
                    if name != '' and position == '':
                        print(f'Warn: position is empty. name: {name}, position: {position}')
                    continue
                name_dict.update({name: position})
        return name_dict

    def __debug_node(self, node):
        from lxml import etree
        return etree.tostring(node, pretty_print=True).decode()

def dump_file(writer, rows):
    for row in rows:
        writer.writerow(row)
