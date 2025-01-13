import sys
import re
import logging
import math
import unicodedata
import unicodeblock.blocks
import pandas as pd
import numpy as np
from fuzzywuzzy import fuzz
from dask.threaded import get
from django.utils.translation import gettext as _
from edtf import parse_edtf, text_to_edtf
from ltldoorstep.reports.report import Report
from ltldoorstep.processor import DoorstepProcessor
from ltldoorstep.reports.report import combine_reports

#summarize_df(df)

def detect_date_columns(df):
    """
    Detects columns in a DataFrame that are likely to contain date information.

    Parameters:
        df (pd.DataFrame): The input DataFrame.

    Returns:
        list: A list of column names that are likely to contain dates.
    """
    date_columns = []
    
    # Keywords to look for in column names
    date_keywords = ["date", "time", "month", "year", "day"]
    
    # Compile regex patterns for strict date formats
    date_patterns = [
        r"^\d{1,2}[/-]\d{1,2}[/-]\d{2,4}$",  # Matches DD/MM/YYYY or MM-DD-YYYY etc.
        r"^\d{4}[/-]\d{1,2}[/-]\d{1,2}$",    # Matches YYYY-MM-DD etc.
        r"^\d{1,2}[/-]\d{1,2}$",              # Matches DD/MM or MM-DD
        r"^\d{4}$",                           # Matches YYYY
        r"^\d{1,2}$"                          # Matches MM or DD
        r"^\d{1,2}\.?\d{4}$",               # Matches MM.YYYY
        r"^\d{4}\.\d{4}$"                   # Matches YYYY.YYYY
    
    ]

    # Function to check if a value matches any date pattern
    def is_date_like(value):
        if pd.isnull(value):
            return False
        value_str = str(value)
        for pattern in date_patterns:
            if re.fullmatch(pattern, value_str):
                return True
        return False
    
    # Loop through columns to detect potential date columns
    for col in df.columns:
        col_lower = col.lower()

                    
        # Handle numeric columns that resemble years
        if pd.api.types.is_numeric_dtype(df[col]):
            temp_col = df[col].dropna().astype(str).str.extract(r"(\d{4})")[0]
            if temp_col.notna().mean() > 0.5:  # If more than 50% resemble years
                date_columns.append(col)
                #print("c", col)
                continue
                
        # Check the data in the column strictly
        if df[col].apply(is_date_like).mean() > 0.5:  # If more than 50% of the column matches date patterns
            date_columns.append(col)
            #print("b", col)
            continue

        # Check column name for keywords with fuzzy matching
        if any(fuzz.partial_ratio(col_lower, keyword) > 80 for keyword in date_keywords):
            date_columns.append(col)
            #print("a", col)
            continue

        # Check the data in the column strictly
        if df[col].apply(is_date_like).mean() > 0.5:  # If more than 50% of the column matches date patterns
            date_columns.append(col)
            #print("b", col)

    return date_columns

#date_cols = detect_date_columns(df)


def convert_to_edtf(value):
    """
    Convert input value to a valid EDTF string if possible.
    
    Parameters:
        value (str or float): The input value to convert. Can be a year, date, or approximation.
        
    Returns:
        str: The converted EDTF string or the original value if it's already valid.
    """
    
    # Check if the value is a single year (e.g., "1971", "1971.0")
    if isinstance(value, (str, float)):
        value_str = str(value).strip()
        
        # Check if it's a year (integer or float, like "1971" or "1971.0")
        #if re.match(r"^\d{4}(\.0+)?$", value_str):  # Matches a 4-digit year, with or without .0
        #    return f"{value_str.split('.')[0]}~"  # Convert to EDTF approximation (e.g., '1971~')
        
        # Handle cases like "10.1978" (this should convert to "1978-10~")
        if re.match(r"^\d{1,2}\.\d{4}$", value_str):  # Matches a fractional year like "10.1978"
            month, year = value_str.split('.')
            return f"{year}-{month.zfill(2)}~"  # Convert to EDTF format for year and month (e.g., '1978-10~')
    
    # If the value is already a valid EDTF string, return it as is
    if isinstance(value, str) and re.match(r"^\d{4}-\d{2}-\d{2}$", value):
        return value  # Already a valid EDTF date in the format YYYY-MM-DD
    
    # Handle approximate dates, e.g., '1971~' or '1971-?'
    if isinstance(value, str):
        if value.endswith('~'):
            return value  # Return if it's already in the approximate format
        if re.match(r"^\d{4}-\d{2}-\?$", value):
            return value  # Return if it's already a partial date with unknown day

    # If the value doesn't match any known patterns, return as is
    #return str(value)  # Return the original value if no transformation is needed


def arches_guess(date, rprt, column_name, row, column):
    """
    Convert input value to a valid Arches acceptable EDTF string if possible.
    
    Parameters:
        value (str or float): The input value to convert. Can be a year, date, or approximation. Name of the date column, row & column for value.
        
    Returns:
        str: The converted EDTF string or the original value if it's already valid, including raising the errors if any changes are required.
    """
    value_str = str(date).strip()
    if re.match(r"^\d{4}(\.0+)?$", value_str):
        pass
    else:
        try:
            date = parse_edtf(date)
        except Exception as e:
            rprt.add_issue(
                logging.WARNING,
                'Date-category',
                "Unsupported date found: Not EDTF",
                error_data={
                    'Value': date,
                    'column-name': column_name,
                    'row-id': row+1,
                    'col-id': column+1,
                    'Suggested Accepted Value': convert_to_edtf(date)
                    #'Suggested Accepted Value': (parse_edtf(convert_to_edtf(date)))
                }
            )
    return date

def check_date(df, rprt):
    """
    Checks the dataframe for valid dates.
    
    Parameters:
    df (pd.DataFrame): The input DataFrame.
    rprt: The report object with an add_issue method.
    
    Returns:
        str: The report including raising the errors if any changes are required.
    """
    
    date_cols = detect_date_columns(df)
    for j in date_cols:
        list_date = df[j].tolist()
        column_name = j
        column_index = df.columns.get_loc(column_name)

        list_edit = [0]*len(df)
        for i in range(0,len(list_date)):
            if not isinstance(list_date[i], float) or not math.isnan(list_date[i]):
                y = str(list_date[i])
                value = str(arches_guess(y, rprt, column_name, i, column_index))
                list_edit[i] = value
                
        return rprt


def max_unique_ratio(df):
    """
    Checks the dataframe for the column that has the closest proximity to become a unique identifier.
    
    df (pd.DataFrame): The input DataFrame.
    
    Returns:
       value (str or float): Name of the column, existing unique value counts & ratio for column vs data length.
    """

    # Get the unique value counts for each column
    unique_counts = df.nunique()
    
    # Find the column with the maximum number of unique values
    max_unique_column = unique_counts.idxmax()
    max_unique_count = unique_counts.max()

    # Calculate the ratio of unique values to the total length of the dataset
    total_length = len(df)
    ratio = max_unique_count / total_length
    result = {
        "max_unique_column": max_unique_column,
        "max_unique_count": max_unique_count,
        "ratio": ratio
    }

    return result


def check_ids_unique(df, rprt):
    """
    Checks if the DataFrame has one column with all unique entries.

    Parameters:
        df (pd.DataFrame): The DataFrame to check.
        rprt: The report object with an add_issue method.

    Returns:
        bool: True if the DataFrame has exactly one column with all unique entries, False otherwise.
    """
    unique_columns = []

    for column in df.columns:
        # Check if the column has unique values and no missing values
        if df[column].is_unique and not df[column].isnull().any():
            unique_columns.append(column)

    if len(unique_columns) == 1:
        return True
    else:
        rprt.add_issue(
            logging.WARNING,
            'DataFrame-Integrity',
            "No single column with all unique entries or multiple unique columns found",
            error_data={
                'total-columns': df.shape[1],
                'unique-columns': unique_columns,
                'row-count': len(df),
                'Suggested Accepted Change - add the missing identification for the entries in the column with highest unique values': max_unique_ratio(df)
            }
        )
        return rprt

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
    """
    Checks the Unicode character blocks in the string columns of the DataFrame and reports any unknown or unsupported character types.

    Parameters:
        csv (pd.DataFrame): The DataFrame to check. Only string columns will be analyzed for their Unicode character blocks.
        rprt: The report object with an add_issue method used to log warnings and issues.

    Returns:
        rprt: The updated report object with warnings about unknown character types and the identified Unicode character blocks.
    """
    
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

def set_properties(df, rprt):
    rprt.set_properties(headers=list(df.columns))
    return rprt

class DateCheckerProcessor(DoorstepProcessor):
    preset = 'tabular'
    code = 'crimson-csv-custom-example:1'
    description = _("CSV Checker Processor")

    def get_workflow(self, filename, metadata={}):
        workflow = {
            'load-csv': (pd.read_csv, filename),
            'step-A': (check_date, 'load-csv', self.make_report()),
            'step-B': (check_ids_unique, 'load-csv', self.make_report()),
            'step-C': (check_character_blocks, 'load-csv', self.make_report()),
            'condense': (workflow_condense, 'step-A', 'step-B', 'step-C'),
            'output': (set_properties, 'load-csv', 'condense')
        }
        return workflow

def workflow_condense(base, *args):
    return combine_reports(*args, base=base)

processor = DateCheckerProcessor


if __name__ == "__main__":
    argv = sys.argv
    processor = DateCheckerProcessor()
    workflow = processor.build_workflow(argv[1])
    print(get(workflow, 'output'))


