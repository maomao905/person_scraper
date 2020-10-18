import re
import pandas as pd

PATTERN_SPACE = re.compile('\s')
PATTERN_PARENTHESE = re.compile('(（|\().*')
PATTERN_FOREIGNER = re.compile('[A-Za-z]*(?<=\[).*?(?=\])')
PATTERN_POSITION = re.compile('.*(執行役員|CEO|ＣＥＯ|社長|責任者)')
# PATTERN_VALID_NAME = regex.compile('^[\p{Script=Han}\p{Script=Hiragana}\p{Script=Katakana}・]+$')

def _get_exclude_names():
    with open('exclude_names.txt', 'r') as f:
        return [w.strip() for w in f.readlines()]

def _remove_parentheses(name):
    name = PATTERN_PARENTHESE.sub('', name)
    return name

def _remove_space(name):
    return PATTERN_SPACE.sub('', name)

def _clean_foreigner_name(name):
    """
    e.g.) extract 'リチャード Ｒ．ルーリー' from 'NicholasBenes[リチャード Ｒ．ルーリー] '
    """
    ma = PATTERN_FOREIGNER.search(name)
    return ma.group(0) if ma is not None else name

def _remove_position(name):
    """
    e.g.) extract '角一幸' from '社長執行役員角一幸'
    """
    return PATTERN_POSITION.sub('', name)

def clean(name):
    name = _remove_parentheses(name)
    name = _remove_space(name)
    name = _clean_foreigner_name(name)
    name = _remove_position(name)
    return name

def main(edinet_input_path, wiki_input_path, output_path):
    exclude_names = _get_exclude_names()
    df_edinet = pd.read_csv(edinet_input_path)
    df_wiki = pd.read_csv(wiki_input_path, names=['name'])

    df_edinet.pipe(
        lambda df: df[~((df.name.isnull())|(df.position.isnull()))]
    ).assign(
        name=lambda df: df.name.apply(clean)
    ).pipe(
        lambda df: pd.concat([df, df_wiki], sort=False)
    ).pipe(
        lambda df: df[(df.name.str.len() > 2) & \
            (~df.name.str.contains('[A-Za-z0-9。、,?？.*]')) & \
            (~df.name.str.contains('^[ぁ-ゞー・〜]+$')) & \
            (~df.name.isin(exclude_names))]
    ).pipe(
        lambda df: pd.DataFrame(df.name.unique())
    ).to_csv(
        output_path,
        index=False,
        header=False,
    )

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--edinet-input-path',
        '-edinet',
        required=True,
        help='path of csv file which you extracted from EDINET',
    )
    parser.add_argument(
        '--wiki-input-path',
        '-wiki',
        required=True,
        help='path of file which you extracted from Wikipedia',
    )
    parser.add_argument(
        '--output-path',
        '-o',
        required=True,
        help='Output csv file path'
    )
    args = parser.parse_args()
    main(args.edinet_input_path, args.wiki_input_path, args.output_path)
