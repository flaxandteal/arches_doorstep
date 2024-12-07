import logging
import numpy as np
import pandas as p
import os

try:
    from django.utils.translation import gettext as _
except ImportError:
    _ = str

from presidio_structured import PandasAnalysisBuilder
from ltldoorstep.processor import DoorstepProcessor
from ltldoorstep.reports.report import combine_reports

LANG = os.environ.get("PII_LANG", "en")
# This function will return the results of a csv file to find personally identifable info(PII)
def return_report(csv, rprt):
    tabular_analysis = PandasAnalysisBuilder().generate_analysis(csv)
    for column, entity in tabular_analysis.entity_mapping.items():
        rprt.add_issue(
            logging.WARNING,
            'pii-entities',
            _("Column {column} identified as containing {entity}").format(column=column, entity=entity),
            column_number=list(csv.columns).index(column),
        )
    return rprt

def set_properties(df, rprt):
    rprt.set_properties(headers=list(df.columns))
    return rprt

def workflow_condense(base, *args):
    return combine_reports(*args, base=base)

class PIICheckerProcessor(DoorstepProcessor):
    preset = 'tabular'
    code = 'pii-checker:1'
    description = _("PII Processor")

    # This function will return the workflow taken from return_report, feeds a csv file into return_report
    def get_workflow(self, filename, metadata={}):
        workflow = {  # Setting up workflow dict...
            'load-csv': (p.read_csv, filename),  # Using Pandas library to read csv file passed in, and also pass the filename
            'report': (set_properties, 'load-csv', self.make_report()),
            'step-A': (return_report, 'load-csv', 'report'),  # Using return_report and loading csv file....
            'output': (workflow_condense, 'step-A')
        }

        return workflow  # Returns workflow dict

processor = PIICheckerProcessor.make
