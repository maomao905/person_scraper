This repository is for scraping and extracting person names (mainly Japanese).
It scrapes executive names from EDINET and person names from Wikipedia and finally merge them.

### Extract executive names from EDINET
- Scrape sources from EDINET.
  - Scraping for 1 year is usually enough to get names of all companies.
```sh
$ python edinet/scrape_sources.py --since 'xxxx-xx-xx' --output-dir=<output sources dir>
```
- Extract executive names from the sources you get above.  (about 30,000 names)
```sh
python edinet/extract.py --sources-dir=<sources dir> --output-path=<output path>
```

### Extract person names from Wikipedia
- Download japanese wikipedia data.
```sh
$ curl -LO https://dumps.wikimedia.org/jawiki/latest/jawiki-latest-pages-articles.xml.bz2
```
- Extract names from wikipedia. (about 120,000 names)
```sh
$ python extract_names.py --input=<path to jawiki-latest-pages-articles.xml.bz2> --output=<output path> -only-kanji-hiragana -exclude-short-name
```

### Clean & Merge
- Clean names and merge two name data of EDINET and Wikipedia.
```sh
$ python clean.py --edinet-input-path=<path to edinet names file> --wiki-input-path=<path to wiki names file> --output-path=<output path>
```

### License
MIT
