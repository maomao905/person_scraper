import bz2
import re, regex

REGEX_PAGE_START = regex.compile('^\s+\<page\>')
REGEX_PAGE_END = regex.compile('^\s+\</page\>')
# REGEX_CATEGORY = regex.compile('^(?=.*\[\[Category:)(?=.*人物)(?!.*関(連|す))')
# REGEX_CATEGORY = regex.compile('\[\[Category:.*(人物|年生|年没)')
REGEX_CATEGORY = regex.compile('\[\[Category:存命人物')
REGEX_TITLE = regex.compile('<title>(.+)</title>')
REGEX_HIRAGANA_OR_KANJI = regex.compile('\p{Script=Han}|\p{Script=Hiragana}')
REGEX_PARENTHESE = re.compile('(（|\().*')
REGEX_IRRELEVANCE = re.compile('[:/;]')

def contain_kanji_or_hiragana(text):
    return bool(REGEX_HIRAGANA_OR_KANJI.search(text))

def is_irrelevant(text):
    return bool(REGEX_IRRELEVANCE.search(text))

def is_valid_name(name, only_kanji_hiragana, exclude_short_name):
    if exclude_short_name and len(name) <= 2:
        return False
    if only_kanji_hiragana and not contain_kanji_or_hiragana(name):
        return False
    if is_irrelevant(name):
        return False
    return True

def clean_name(name):
    name = REGEX_PARENTHESE.sub('', name)
    return name.strip()

def save(names, path):
    with open(path, 'w') as f:
        rows = set(f'{name}\n' for name in names)
        f.writelines(rows)

def extract(input_path, output_path, only_kanji_hiragana, exclude_short_name):
    person_names = []
    page_texts = []
    for line in iter_wikidata(input_path):
        if REGEX_PAGE_START.search(line):
            page_texts = []
            continue

        page_texts.append(line)
        if REGEX_PAGE_END.search(line):
            page = ''.join(page_texts)

            if not REGEX_CATEGORY.search(page):
                continue

            title = REGEX_TITLE.search(page).group(1)

            name = clean_name(title)
            if not is_valid_name(name, only_kanji_hiragana, exclude_short_name):
                continue
            person_names.append(name)

    save(person_names, output_path)

def iter_wikidata(input_path):
    if not input_path.endswith('bz2'):
        raise ValueError('extention of the input file must be bz2.')

    with bz2.BZ2File(input_path) as f:
        for line in f:
            yield line.decode('utf-8')

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-input-path',
        '-i',
        required=True,
        help='Wikipedia path(ex:jawiki-YYYYMMDD-pages-articles.xml.bz2)',
    )
    parser.add_argument(
        '-output-path',
        '-o',
        required=True,
        help='output path',
    )
    parser.add_argument(
        '-only-kanji-hiragana',
        action='store_true',
        help='Exclude name which does not contain either Kanji or Hiragana',
    )
    parser.add_argument(
        '-exclude-short-name',
        action='store_true',
        help='Exclude name which has 2 or less chars',
    )
    args = parser.parse_args()

    import time
    start = time.time()
    extract(args.input_path, args.output_path, args.only_kanji_hiragana, args.exclude_short_name)
    end = time.time()
    print(f'took: {end - start}')
