import numpy as np
import json
import gettext
from dask.threaded import get
import sys
import pandas as pd
import re
import logging
import spacy
from django.utils.translation import gettext as _
from spellchecker import SpellChecker
from ltldoorstep.processor import DoorstepProcessor
from ltldoorstep.aspect import AnnotatedTextAspect
from ltldoorstep.reports.report import combine_reports

gettext.install('ltldoorstep')

def spellcheck(csv, rprt, nlp):
    checker = SpellChecker()
    # All characters are Latinate (unicodedata.normalize('NFKD')[0] is Latin)
    for column, series in csv.items():
        if series.dtype == 'object':
            for row_number, doc in enumerate(nlp.pipe([str(cell) for cell in series])):
                column_number = csv.columns.get_loc(column)
                native_row = json.loads(csv.loc[row_number].to_json())

                # results = checker.unknown(cell.split(' '))
                to_check = [tok for tok in doc if tok.pos_ != 'PROPN']
                failed = checker.unknown(map(str, to_check))
                to_note = [(tok, checker.candidates(str(tok))) for tok in doc if str(tok) in failed]
                if to_note:
                    content = AnnotatedTextAspect(doc)
                    issue_text = []
                    for tok, suggestions in to_note:
                        content.add(
                            note=', '.join(suggestions),
                            start_offset=tok.idx,
                            end_offset=tok.idx + len(tok),
                            level=logging.WARNING,
                            tags=['spelling']
                        )
                        issue_text.append(f'"{tok}"')
                    rprt.add_issue(
                        logging.WARNING,
                        'spelling-suggestions',
                        _("Spelling issues with ") + ', '.join(issue_text),
                        column_number=column_number,
                        row_number=row_number,
                        row=native_row,
                        cell_content=content
                    )

    return rprt

def set_properties(df, rprt):
    rprt.set_properties(headers=list(df.columns))
    return rprt

class SpellCheckerProcessor(DoorstepProcessor):
    preset = 'tabular'
    code = 'lintol-spell-checker:1'
    description = _("Spellcheck Processor")

    _spacy_model = 'en_core_web_sm'

    def initialize(self, report=None, context=None):
        self.nlp = spacy.load(self._spacy_model)
        return super().initialize(report, context)

    def get_workflow(self, filename, metadata={}):
        workflow = {
            'load-csv': (pd.read_csv, filename),
            'report': (set_properties, 'load-csv', self.make_report()),
            'step-A': (spellcheck, 'load-csv', 'report', self.nlp),
            'output': (workflow_condense, 'step-A')
        }
        return workflow

def workflow_condense(base, *args):
    return combine_reports(*args, base=base)

processor = SpellCheckerProcessor.make

if __name__ == "__main__":
    argv = sys.argv
    processor = SpellCheckerProcessor()
    processor.initialize()
    workflow = processor.build_workflow(argv[1])
    print(get(workflow, 'output'))
