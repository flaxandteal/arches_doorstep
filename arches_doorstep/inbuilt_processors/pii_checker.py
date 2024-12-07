import logging
import numpy as np
import pandas as p

from django.utils.translation import gettext as _
from piianalyzer.analyzer import PiiAnalyzer
from ltldoorstep.processor import DoorstepProcessor

pii_details = {
    'N': 'name',
    'P': 'phone_no',
    'A': 'address',
    'C': 'credit_card_no',
    'E': 'email_address',
    'O': 'organization'

}


# This function will return the results of a csv file to find personally identifable info(PII)
def return_report(csv):

    piianalyzer = PiiAnalyzer(csv)  # Feeding in csv file to PIIAnalyzer...

    dataset = set()  # set dataset object to set method

    analysis = piianalyzer.analysis()  # Assigning the results of the analysis to analysis var...

    np.vectorize(lambda cell: dataset.update({analysis(a)for a in cell}))

    return {
        'check_pii_detail:pii-found': ('PII details found...', logging.INFO, [pii_details[d[0]] for d in dataset])
    }


class PIICheckerProcessor(DoorstepProcessor):
    preset = 'tabular'
    code = 'pii-checker:1'
    description = _("PII Processor")

    # This function will return the workflow taken from return_report, feeds a csv file into return_report
    def get_workflow(self, filename, metadata={}):
        workflow = {  # Setting up workflow dict...
            'loading': (p.read_csv, filename),  # Using Pandas library to read csv file passed in, and also pass the filename
            'report_returned': (return_report, 'loading'),  # Using return_report and loading csv file....
            'output': (list, ['report_returned'])  # This will be the output
        }

        return workflow  # Returns workflow dict

processor = PIICheckerProcessor.make
