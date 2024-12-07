from ltldoorstep import regex_utils as utils
import time
import numpy as np
import re
import yaml
import dateparser
from ltldoorstep.reports import report
import pandas as p
import sys
from dask.threaded import get
import logging
from django.utils.translation import gettext as _
from ltldoorstep.processor import DoorstepProcessor
from ltldoorstep.reports.report import combine_reports
import chardet
import json
from moneypandas import MoneyArray
from tabulator import Stream
from tablespy.inspector import Inspector

MATCH_RATIO = 0.05
MAX_SAMPLE_SIZE = 1000
MAX_SNIPPET_SIZE = 20
SAMPLE_MAX_AXIS_CHARS = 100
SAMPLE_MAX_LABEL_CHARS = 20

def read_csv(filename):
    with open(filename, 'rb') as f:
        result = chardet.detect(f.read(40000))

    encoding = result['encoding']
    # Rather than risk missing a non-ascii char after chardet bytes
    # at least try Unicode to begin
    if encoding == 'ascii':
        encoding = 'utf-8'

    retry = False
    while True:
        try:
            time.sleep(30)
            data = p.read_csv(
                filename,
                encoding=encoding,
                low_memory=True,
                comment='#',
                na_values=('*',),
                keep_default_na=True
            )
            break
        except UnicodeDecodeError:
            if retry:
                break
            # If we didn't get the encoding right the first
            # time, try the whole file
            with open(filename, 'rb') as f:
                result = chardet.detect(f.read())
            encoding = result['encoding']
            retry = True

    data.index.name = 'Row'
    return {(None, None): data}

def read_other(filename):
    with open(filename, 'rb') as f:
        result = chardet.detect(f.read(1024))

    inspector = Inspector(filename)
    datas = {}
    sheets = set()
    for region_df, region, sheet in inspector.region_iter(encoding=result['encoding']):
        table = [int(t) for t in region['lower-left']]
        table += [int(t) for t in region['upper-right']]
        datas[(sheet, tuple(table))] = region_df
        sheets.add(sheet)

    if len(sheets) == 1:
        datas = {(None, tuple(table)): data for (sheet, table), data in datas.items()}

    return datas

def json_loader(filename):
    with open(filename, 'r') as f:
        read = json.load(f)
    return read

def json_walk(iterable, matcher, match, total, skip_it=None):
    for elt in iterable:
        if isinstance(elt, tuple):
            key = elt[0]
            elt = elt[1]
        else:
            key = None

        if isinstance(elt, list):
            match, total = json_walk(elt, matcher, match, total, skip_it)
        elif isinstance(elt, dict):
            match, total = json_walk(elt.items(), matcher, match, total, skip_it)
        else:
            if skip_it is not None:
                if next(skip_it):
                    total += 1
                    if matcher and matcher(elt, key):
                        match += 1
            else:
                total += 1

    return match, total

def is_this_spatial_csv(datas, context):
    keywords = {'lat', 'lng', 'northing', 'easting', 'latitude', 'longitude', 'coordinates', 'coord'}
    value_res = {utils.get_regex('uk-postcode'), utils.get_regex('common-street-indicators')}

    match = 0
    total = 0

    key_matcher = lambda k: isinstance(k, str) and any({kw in k.lower() for kw in keywords})
    header_match = 0

    matcher = lambda x: isinstance(x, str) and any({rex.search(x.lower()) for rex in value_res})

    data_match = 0
    for loc, data in datas.items():
        data_sample = data.sample(MAX_SAMPLE_SIZE) if MAX_SAMPLE_SIZE < len(data) else data
        header_match += len([d for d in data.columns if key_matcher(d)])
        for ix, row in data_sample.iterrows():
            if any([matcher(x) for x in row]):
                data_match += 1
            total += len(row)

    return 30 * header_match + 10 * data_match, total

def is_this_spatial_json(data, context):
    keywords = {'lat', 'lng', 'northing', 'easting', 'latitude', 'longitude', 'coordinates', 'coord'}

    _, total = json_walk([data], None, 0, 0, None)

    skip = np.full((total,), False)
    skip[np.random.choice(total, size=min(total, MAX_SAMPLE_SIZE), replace=False)] = True

    matcher = lambda x, k: isinstance(k, str) and any({kw in k.lower() for kw in keywords})

    match, total = json_walk([data], matcher, 0, 0, iter(skip))

    return match, total

re_likely_datetime = utils.get_regex('search-basic-date-time')
def is_datetime(x, k):
    return isinstance(x, str) and len(x) > 3 and re_likely_datetime.search(x) and dateparser.parse(x) is not None

def is_datetime_deep(x, k):
    return isinstance(x, str) and len(x) > 3 and dateparser.parse(x) is not None

def is_this_timeseries_csv(datas, context):
    keywords = {'year', 'month', 'hour', 'day', 'minute'}

    match = 0
    total = 0

    matcher = lambda k: isinstance(k, str) and any({kw in k.lower() for kw in keywords})
    header_match = 0
    data_match = 0
    row_match = 0

    for loc, data in datas.items():
        header_match += len([d for d in data.columns if matcher(d)])
        sample_row_names = data.index[np.random.choice(len(data), size=min(len(data), int(MAX_SAMPLE_SIZE / 10)), replace=False)]
        row_match += len([d for d in sample_row_names if is_datetime_deep(d, None)])

        data_sample = data.sample(MAX_SAMPLE_SIZE) if MAX_SAMPLE_SIZE < len(data) else data
        for ix, row in data_sample.iterrows():
            if any([is_datetime(x, k) for k, x in row.items()]):
                data_match += 1
            total += len(row)

        sqrt_sample = int(np.sqrt(MAX_SAMPLE_SIZE))
        data_sample = data.sample(sqrt_sample) if sqrt_sample < len(data) else data
        for ix, row in data_sample.iterrows():
            sample = row.sample(sqrt_sample) if len(row) > sqrt_sample else row
            if any([is_datetime_deep(x, k) for k, x in sample.items()]):
                data_match += 1
            total += len(sample)

    return 100 * row_match + 30 * header_match + 10 * data_match, total

def find_index_column(rprt, datas, context):
    for (sheet, table), data in datas.items():
        unique_column_types = (np.int64, object, np.datetime64)
        col1_type = data.iloc[:, 0].dtype
        col2_type = data.iloc[:, 1].dtype if len(data.columns) > 1 else None
        index_text = _("This dataset was indexed, by default, by row count")
        error_data = []
        if col1_type in unique_column_types:
            if len(data.iloc[:, 0].unique()) == len(data):
                data.index = data.iloc[:, 0]
                data.index.name = data.columns[0]
                error_data = [[data.columns[0], str(col1_type)]]

                index_text = _("This dataset can be indexed by its first ({}:{}) column").format(data.columns[0], error_data[0][1])
            elif col2_type is not None and col2_type in unique_column_types and len(data.iloc[:, 0:2].drop_duplicates()) == len(data):
                data.index = data.iloc[:, 0].astype(str) + '-' + data.iloc[:, 1].astype(str)
                data.index.name = data.columns[0] + ' + ' + data.columns[1]
                error_data = [[data.columns[0], str(col1_type)], [data.columns[1], str(col2_type)]]
                index_text = _("This dataset can be indexed by its first two ({}:{} and {}:{}) columns").format(data.columns[0], error_data[0][1], data.columns[1], error_data[1][1])

        rprt.add_issue(
            logging.INFO,
            'index-guess',
            index_text,
            sheet=sheet,
            table=table,
            error_data=error_data,
            at_top=True
        )

    return datas
    #if data.iloc[:, 0].dtype in (np.int64, np.datetime

def find_special_columns(rprt, datas, context):
    _currency_indications = {
        r'£': 'GBP',
        r'\bGBP\b': 'GBP',

        r'€': 'EUR',
        r'\bEUR\b': 'EUR',

        r'\$': 'USD',
        r'\bUSD\b': 'USD'
    }

    for (sheet, table), data in datas.items():
        columns = {}
        for sym, cur in _currency_indications.items():
            for label, content in data.iteritems():
                if not label:
                    continue
                data_sample = content.sample(MAX_SNIPPET_SIZE) if MAX_SNIPPET_SIZE < len(content) else content

                if data_sample.apply(lambda x: re.search(sym, str(x))).count() > len(data_sample) / 2:
                    columns[label] = cur
                elif re.search(sym, str(label)):
                    columns[label] = cur

        if columns:
            rprt.add_issue(
                logging.INFO,
                'currency-guess',
                _("Column(s) appear to be currency: {}").format(', '.join(columns)),
                error_data=columns,
                sheet=sheet,
                table=table,
                at_top=True
            )

            for col, cur in columns.items():
                data[col] = MoneyArray(data[col], default_money_code=cur, errors='coerce')

    return datas

def find_category_columns(rprt, datas, context):
    for (sheet, table), data in datas.items():
        category_column_types = (np.int64, object)
        category_col_ratio = 0.5
        category_col_cap = 10
        row_values = {v: set() for v in data.columns}

        def check_row_values(df, row_values):
            for ix, row in df.iterrows():
                for cn, (col, cell) in enumerate(row.iteritems()):
                    if col in row_values and data.iloc[:, cn].dtype in category_column_types and p.notnull(cell):
                        row_values[col].add(cell)
            return row_values

        row_values = check_row_values(data.iloc[0:200], row_values)
        row_values = {v: s for v, s in row_values.items() if len(s) > 1 and len(s) < category_col_ratio * len(data) and len(s) < category_col_cap}
        row_values = check_row_values(data, row_values)
        row_values = {v: s for v, s in row_values.items() if len(s) > 1 and len(s) < category_col_ratio * len(data) and len(s) < category_col_cap}

        columns = [(c, data[c].dtype) for c in row_values]
        rprt.add_issue(
            logging.INFO,
            'category-columns',
            _("There are {} category candidates ({})").format(len(row_values), '; '.join([f'{c}:{t}' for c, t in columns])),
            sheet=sheet,
            table=table,
            error_data={c: (str(t), list(row_values[c])) for c, t in columns}
        )

        for c, t in columns:
            data[c] = data[c].astype('category')

    return datas

def find_numeric_columns(rprt, datas, context):
    sample_columns = {}
    for (sheet, table), data in datas.items():
        numeric_columns = list(data.select_dtypes(include=['number']).columns)
        float_columns = list(data.select_dtypes(include=['number']).columns)

        def _score_column(col):
            weight = 1
            if 'num' in col.lower():
                weight = 2

            if col in float_columns:
                weight *= 2

            weight *= data[col].count() / len(data[col])
            return weight

        if len(numeric_columns) > 1:
            sample_columns[(sheet, table)] = sorted(numeric_columns[1:], key=_score_column) # Avoid any index column, as the most likely first
        else:
            sample_columns[(sheet, table)] = []

        rprt.add_issue(
            logging.INFO,
            'numeric-columns',
            _("This dataset has {} numeric columns, with {} floats").format(len(numeric_columns), len(float_columns)),
            error_data=numeric_columns,
            sheet=sheet,
            table=table,
            at_top=True
        )

        rprt.add_issue(
            logging.INFO,
            'row-column-count',
            _("This dataset has {} rows and {} columns").format(data.shape[0], data.shape[1]),
            error_data=list(data.shape),
            sheet=sheet,
            table=table,
            at_top=True
        )

    return sample_columns, datas

def generate_sample(rprt, info, context):
    sample_columns, datas = info

    samples = []

    for (sheet, table), data in datas.items():
        data_sample = data.sample(MAX_SNIPPET_SIZE) if MAX_SNIPPET_SIZE < len(data) else data

        if data_sample.index.name:
            index_name = data_sample.index.name
        else:
            index_name = None

        if (sheet, table) in sample_columns and sample_columns[(sheet, table)]:
            sample_table_columns = sample_columns[(sheet, table)]
            data_sample_list = data_sample[sample_table_columns[-1]].dropna().sort_index()
            rows = []
            axis_chars = 0
            for row in data_sample_list.index:
                if len(str(row)) <= SAMPLE_MAX_LABEL_CHARS:
                    axis_chars += len(str(row))
                    if axis_chars > SAMPLE_MAX_AXIS_CHARS:
                        break
                    rows.append(row)
            if rows:
                data_sample_list = data_sample_list.loc[rows]

            if len(data_sample_list):
                samples.append([
                    _("Extract for numeric column {} of {} entries").format(sample_table_columns[-1], len(data_sample_list)),
                    {
                        'type': 'numeric',
                        'name': sample_table_columns[-1],
                        'index': list(data_sample_list.index),
                        'indexName': index_name,
                        'values': data_sample_list.tolist()
                    }
                ])

            money_columns = [col for col in data.columns if str(data[col].dtype) == 'money']
            if money_columns:
                data_sample_list = data_sample[money_columns[0]].dropna()
                if len(data_sample_list):
                    total = data_sample_list.sum()
                    samples.append((
                        _("Extract for currency column {} of {} entries").format(money_columns[0], len(data_sample_list)),
                        {
                            'type': 'currency',
                            'name': money_columns[0],
                            'total': float(total.amount),
                            'index': list(data_sample_list.index),
                            'indexName': index_name,
                            'currency': total.currency,
                            'values': [float(x.amount) for x in data_sample_list.tolist() if x.currency == total.currency]
                        }
                    ))

            category_columns = [col for col in data.columns if str(data[col].dtype) == 'category']
            if category_columns:
                data_sample_list = data[category_columns[0]].dropna()
                if len(data_sample_list) and len(data_sample_list.unique()) < MAX_SNIPPET_SIZE:
                    totals = data_sample_list.value_counts().sort_index()
                    samples.append((
                        _("Summary of category column {} of {} categories").format(category_columns[0], len(totals)),
                        {
                            'type': 'category',
                            'name': category_columns[0],
                            'entries': [str(x) for x in totals.index],
                            'values': [int(x) for x in totals]
                        }
                    ))

    if samples:
        samples = list(zip(*samples))
        rprt.add_issue(
            logging.INFO,
            'data-sample',
            '; '.join(samples[0]),
            error_data=samples[1],
            sheet=sheet,
            table=table
        )

    return rprt

def is_this_timeseries_json(data, context):
    matcher = is_datetime

    _, total = json_walk([data], None, 0, 0, None)

    skip = np.full((total,), False)
    skip[np.random.choice(total, size=min(total, MAX_SAMPLE_SIZE), replace=False)] = True

    match, total = json_walk([data], matcher, 0, 0, iter(skip))

    return match, total

class DtComprehenderProcessor(DoorstepProcessor):
    preset = 'tabular'
    code = 'datatimes/dt-comprehender:1'
    description = 'Infer the nature of the data searched'

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

                    self._report.add_issue(
                        log_level,
                        error['code'],
                        error['message'],
                        row_number=row_number,
                        column_number=column_number,
                        row=row
                    )

        return self._report

    @staticmethod
    def make_report():
        return report.TabularReport(
            'datatimes/dt-comprehender:1',
            _("Data Times processor to infer the nature of a dataset")
        )

    def get_workflow(self, filename, context):
        fmt = None

        if filename.endswith('csv'):
            fmt = 'csv'
        elif filename.endswith('ods'):
            fmt = 'ods'
        elif filename.endswith('xls'):
            fmt = 'xls'
        elif filename.endswith('geojson'):
            fmt = 'geojson'
        elif filename.endswith('json'):
            fmt = 'json'
        elif context.resource and 'filetype' in context.resource:
            if 'csv' in context.resource['filetype'].lower():
                fmt = 'csv'
            elif any([xls in context.resource['filetype'].lower() for xls in ('xlsx', 'excel', 'xls')]):
                fmt = 'xls'
            elif 'geojson' in context.resource['filetype'].lower():
                fmt = 'geojson'
            elif 'json' in context.resource['filetype'].lower():
                fmt = 'json'
            elif 'ods' in context.resource['filetype'].lower():
                fmt = 'ods'

        logging.error(fmt)

        # setting up workflow dict
        full_flow = False
        if fmt in ('ods', 'xls', 'csv'):
            spatial = is_this_spatial_csv
            timeseries = is_this_timeseries_csv
            read = read_csv if fmt == 'csv' else read_other
            full_flow = True
        elif fmt == 'geojson':
            spatial = lambda *args: (1, 1)
            read = json_loader
            timeseries = is_this_timeseries_json
        elif fmt == 'json':
            spatial = is_this_spatial_json
            timeseries = is_this_timeseries_json
            read = json_loader
        else:
            spatial = is_this_spatial_csv
            timeseries = is_this_timeseries_csv
            read = read_other

        workflow = {
            'data': (read, filename),
            'spatial': (spatial, 'data', self.context),
            'timeseries': (timeseries, 'data', self.context),
            'classify': (classify, self._report, 'spatial', 'timeseries'),
            'output': (set_properties, 'data', 'classify')
        }

        if full_flow:
            workflow.update({
                'findindexcolumn': (find_index_column, self._report, 'data', self.context),
                'findcategorycolumns': (find_category_columns, self._report, 'findindexcolumn', self.context),
                'findspecialcolumns': (find_special_columns, self._report, 'findcategorycolumns', self.context),
                'findnumericcolumns': (find_numeric_columns, self._report, 'findspecialcolumns', self.context),
                'generatesample': (generate_sample, self._report, 'findnumericcolumns', self.context),
                'condense': (workflow_condense, 'classify', 'generatesample'),
                'output': (set_properties, 'data', 'condense')
            })

        return workflow

def set_properties(datas, rprt):
    rprt.set_properties(headers=sum([list(df.columns) for df in datas.values()], []))
    return rprt

def workflow_condense(base, *args):
    # rprt = combine_reports(*args, base=base)
    # There's only one report, so combining it with itself leads to duplication
    return base

def classify(rprt, spatial_pair, timeseries_pair):
    types = {
        'spatial': spatial_pair,
        'timeseries': timeseries_pair
    }
    tags = []

    for typ, (match, total) in types.items():
        if total < 1e-10:
            continue

        include = match / total > MATCH_RATIO

        if include:
            tags.append(typ)
        types[typ] = (match, total, include)

        rprt.add_issue(
            logging.INFO,
            f'comprehension-type-{typ}',
            _("The {} match ratio is {} = {} / {}").format(typ, match / total, match, total),
            error_data=(match, total, MATCH_RATIO)
        )

    rprt.add_issue(
        logging.INFO,
        'all-comprehension-type-tags',
        _("This dataset appears to be: {}").format(', '.join(tags)),
        error_data=tags,
        at_top=True
    )

    return rprt

processor = DtComprehenderProcessor.make

if __name__ == "__main__":
    argv = sys.argv
    processor = DtComprehenderProcessor()
    workflow = processor.build_workflow(argv[1])
    print(get(workflow, 'output'))
