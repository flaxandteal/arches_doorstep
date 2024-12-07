from goodtables import validate
import sys
from dask.threaded import get
import logging
from ltldoorstep.processor import DoorstepProcessor

class GoodTablesProcessor(DoorstepProcessor):
    preset = 'tabular'
    code = 'frictionlessdata/goodtables-py:1'
    description = _("Processor wrapping Frictionless Data's Goodtables")

    def structure_report(self, report):
        results = {}

        levels = {
            'errors': logging.ERROR,
            'warnings': logging.WARNING,
            'informations': logging.INFO
        }

        table = report['tables'][0]
        self._report.set_properties(
            row_count=table['row-count'],
            headers=table['headers']
        )
        for level, log_level in levels.items():
            if level in table and table[level]:
                for error in table[level]:
                    row_number = error['row-number'] if 'row-number' in error else None
                    column_number = error['column-number'] if 'column-number' in error else None
                    row = error['row'] if 'row' in error else None

                    print(error)
                    self._report.add_issue(
                        log_level,
                        error['code'],
                        error['message'],
                        row_number=row_number,
                        column_number=column_number,
                        row=row
                    )

        return self._report

    def get_workflow(self, filename, metadata={}):
        workflow = {
            'validate': (validate, filename),
            'output': (self.structure_report, 'validate')
        }

        return workflow

processor = GoodTablesProcessor.make

if __name__ == "__main__":
    argv = sys.argv
    processor = GoodTablesProcessor()
    workflow = processor.build_workflow(argv[1])
    print(get(workflow, 'output'))
