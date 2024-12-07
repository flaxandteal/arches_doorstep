import numpy as np
from dask.threaded import get
import sys
import pandas as pd
import re
import unicodedata
import unicodeblock.blocks
import logging
from ltldoorstep.processor import DoorstepProcessor
from ltldoorstep.reports.report import combine_reports

unicode_category_major = {
    'L': ('letter'),
    'M': ('mark'),
    'N': ('number'),
    'P': ('punctuation'),
    'S': ('symbol'),
    'Z': ('separator'),
    'C': ('control character')
}


def check_character_blocks(csv, rprt):
    # All characters are Latinate (unicodedata.normalize('NFKD')[0] is Latin)
    string_csv = csv.select_dtypes(include=['object'])

    block_set = set()
    # consider double @functools.lru_cache(maxsize=128, typed=False) if required
    string_csv.apply(np.vectorize(lambda cell: block_set.update({unicodeblock.blocks.of(c) for c in cell}) if type(cell) is str else ''))

    if None in block_set:
        block_set.remove(None)
        rprt.add_issue(
            logging.WARNING,
            'unknown-category',
            ("Unknown character type found")
        )

    rprt.add_issue(
        logging.WARNING,
        'blocks-found',
        ("Character blocks found") + ': ' + ', '.join(block_set),

    )

    return rprt

def check_character_categories(csv, rprt):
    # All characters are Latinate (unicodedata.normalize('NFKD')[0] is Latin)
    string_csv = csv.select_dtypes(include=['object'])
    categories = set()
    # consider double @functools.lru_cache(maxsize=128, typed=False) if required
    string_csv.apply(np.vectorize(lambda cell: categories.update({unicodedata.category(c) for c in cell}) if type(cell) is str else ''))

    categories_found = [unicode_category_major[c[0]] for c in categories]
    rprt.add_issue(
        logging.INFO,
        'categories-found',
        ("Character categories found") + ': ' + ', '.join(categories_found),

    )

    return rprt

def check_std_dev(df, rprt):
    # Standard Deviation is non-negative
    names_for_standard_deviation = [
        r'std[. ]*dev',
        r'standard deviation',
    ]

    bad_rows = {}
    matches = [re.match(rex, col, re.IGNORECASE) for rex in names_for_standard_deviation for col in row.dtypes.index]
    for match in matches:
        col = match[0]
        if col not in bad_rows:
            bad_rows[col] = filter(lambda r: r[col] < 0, csv.iterrows())

    return {
        'check_std_dev:neg-std-dev': ('Rows with negative Standard Deviation', logging.WARNING, bad_rows)
    }

def check_ids_unique(csv, rprt):
    # IDs are unique
    if 'ID' in csv:
        ids = csv['ID']
        min_duplicates = len(set(ids)) < len(ids)
        if min_duplicates > 0:
            rprt.add_issue(
                'lintol/csv-checker:1',
                logging.WARNING,
                'check-ids-unique:ids-not-unique',
                ("IDs are not unique, at least %d duplicates") % min_duplicates,

            )

    return rprt

def set_properties(df, rprt):
    rprt.set_properties(headers=list(df.columns))
    return rprt

def check_ids_surjective(csv, rprt):
    # IDs are surjective onto their range
    if 'ID' in csv:
        ids = csv['ID']
        unique_ids = len(set(ids))
        expected_ids = max(ids) - min(ids) + 1
        if expected_ids != unique_ids:
            rprt.add_issue(
                logging.WARNING,
                'check-ids-surjective:not-surjective',
                ("IDs are missing, %d missing between %d and %d") % (expected_ids - unique_ids, min(ids), max(ids)),
                error_data={
                    'missing-count': expected_ids - unique_ids,
                    'lowest-id': min(ids),
                    'highest-id': max(ids)
                }

            )

class CsvCheckerProcessor(DoorstepProcessor):
    preset = 'tabular'
    code = 'lintol-csv-custom-example:1'
    description = _("CSV Checker Processor")

    def get_workflow(self, filename, metadata={}):
        workflow = {
            'load-csv': (pd.read_csv, filename),
            'step-A': (check_ids_surjective, 'load-csv', self.make_report()),
            'step-B': (check_ids_unique, 'load-csv', self.make_report()),
            'step-C': (check_character_categories, 'load-csv', self.make_report()),
            'step-D': (check_character_blocks, 'load-csv', self.make_report()),
            'condense': (workflow_condense, 'step-A', 'step-B', 'step-B', 'step-D'),
            'output': (set_properties, 'load-csv', 'condense')
        }
        return workflow

def workflow_condense(base, *args):
    return combine_reports(*args, base=base)

processor = CsvCheckerProcessor

if __name__ == "__main__":
    argv = sys.argv
    processor = CsvCheckerProcessor()
    workflow = processor.build_workflow(argv[1])
    print(get(workflow, 'output'))
