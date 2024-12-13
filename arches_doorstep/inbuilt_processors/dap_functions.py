import logging
import sys
import pandas as pd
import numpy as np
import re
import json

from requests import get
from scipy.stats import mode
from ltldoorstep.reports.report import Report
from ltldoorstep.processor import DoorstepProcessor
from ltldoorstep.reports.report import combine_reports
from gettext import gettext as _
from dateutil import parser


pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)


'''
# Separate numeric, date and object data types
numeric_columns = [col for col in df.columns if np.issubdtype(df[col].dtype, np.number)]
object_columns = [col for col in df.columns if df[col].dtype == 'object']
date_columns = [col for col in df.columns if df[col].dtype == 'datetime64[ns]']
'''

def detect_date_columns(df, rprt):
    date_columns = []
    date_keywords = ['date', 'time', 'year', 'month', 'day']  # Add other keywords as needed
    date_patterns = [
        r'\b\d{4}-\d{1,2}-\d{1,2}\b',  # Matches YYYY-MM-DD
        r'\b\d{1,2}/\d{1,2}/\d{4}\b',  # Matches MM/DD/YYYY or DD/MM/YYYY
        r'\b\d{1,2}-\d{1,2}-\d{4}\b',  # Matches MM-DD-YYYY or DD-MM-YYYY
        r'\b\d{4}/\d{1,2}/\d{1,2}\b',  # Matches YYYY/MM/DD
    ]

    for column in list(df.columns):
        if any(keyword in column.lower() for keyword in date_keywords):
            try:
                # parsed_dates = pd.to_datetime(df.loc[:,column], errors='raise')
                date_columns.append(column)
            except (ValueError, TypeError):
                continue
        else:
            try:
                # Check if the column exists and is not empty
                if column in df.columns and not df[column].dropna().empty:
                    sample_values = df.loc[:, column].dropna().astype(str).sample(min(10, len(df.loc[:, column].dropna())), random_state=1)
                    if any(re.search(pattern, value) for pattern in date_patterns for value in sample_values):
                        parsed_dates = pd.to_datetime(df[column], errors='raise')
                        date_columns.append(column)
            except (ValueError, TypeError, KeyError) as e:
                print(f"Error processing column {column}: {e}")
                continue

    rprt.add_issue(
        logging.INFO,
        'dates',
        "Dates",
        error_data=date_columns
    )
    return rprt



def data_info(data, rprt):
    '''
    This function returns the numerical summary, categorical summary 
    and the missing data percentage along with the types of data fields
    It also sends back the shape of the dataset
    
    Input
        data: pandas dataframe for the uploaded data
        
    Output
        shows on page 2, 4 tables
    '''
    data.columns = data.columns.str.replace(' ', '_')
    # Display basic information about the dataset
    #print("Datatypes of the dataset uploaded")
    # Summary statistics for numerical columns
    #print("Statistical Summary (Numerical) of the dataset uploaded")
    numerical_summary = data.describe()
    # Summary statistics for categorical columns
    #print("Statistical Summary (Categorical) of the dataset uploaded")
    categorical_summary = data.describe(include=["object"])
    #print("Missing data percentage in all fields of dataset uploaded")
    # Check for missing data
    missing_data = data.isnull().sum()
    missing_data_percentage = (missing_data / len(data)) * 100
    data_types = data.dtypes
    # Creating a DataFrame to display all the information
    missing_data_info = pd.DataFrame({
        'Missing Data Count': missing_data,
        'Missing Data Percentage': round(missing_data_percentage, 2),
        'Data Type': data_types
    })
    
    numeric_columns = [(n, col, "num") for n, col in enumerate(data.columns) if np.issubdtype(data[col].dtype, np.number)]
    object_columns = [(n, col, "cat") for n, col in enumerate(data.columns) if data[col].dtype == 'object']
    # Get the shape of the dataset
    shape_of_dataset = data.shape
    # Convert the shape information to a DataFrame
    
    # Merge DataFrames using join with how='left'
    merged_df = missing_data_info.join(categorical_summary.T, how='left')
    # Replace NaN with "Not defined"
    merged_df = merged_df.fillna("NA")
    for num, name, typ in numeric_columns + object_columns:
        rprt.add_issue(
            logging.INFO,
            'column-type',
            f"Column type: {name} is {typ}",
            column_number=num,
            error_data={"name": name, "type": typ, "col": num}
        )
    rprt.add_issue(
        logging.INFO,
        'numerical-summary',
        "Numerical summary",
        error_data=numerical_summary.to_json()
    )
    rprt.add_issue(
        logging.INFO,
        'shape',
        "Shape df",
        error_data={'Rows': [shape_of_dataset[0]], 'Columns': [shape_of_dataset[1]]}
    )
    rprt.add_issue(
        logging.INFO,
        'more-information',
        "More information",
        error_data=merged_df.T.to_json(default_handler=str),
    )
    # shape_df.to_json(), numerical_summary.to_json(), merged_df.T.to_json(default_handler=str), nums.to_json(), cats.to_json(), dates.to_json()

    # return [
    #     shape_df.to_json(),
    #     numerical_summary.to_json(),
    #     merged_df.T.to_json(default_handler=str),
    #     nums.to_json(),
    #     cats.to_json(),
    # ]
    return rprt

def parse_dates(df):
    # Convert columns with datetime objects to 'yyyy-mm-dd' format
    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            # Convert to the 'yyyy-mm-dd' format and convert to string
            df[col] = df[col].dt.strftime('%Y-%m-%d')
    return df

def read_dataset(file):
    """
    Reads a dataset from a given file, supporting both CSV and Excel formats.
    
    Parameters:
    file (str or UploadFile): The file path or uploaded file.
    
    Returns:
    pd.DataFrame: The loaded dataset.
    """
    
    if isinstance(file, str):  # If file is a file path
        if file.endswith('.csv'):
            return pd.read_csv(file)
        elif file.endswith(('.xls', '.xlsx')):
            return pd.read_excel(file)
        else:
            raise ValueError("Unsupported file format. Please provide a CSV or Excel file.")
    elif hasattr(file, 'filename'):  # If file is an uploaded file object
        if file.filename.endswith('.csv'):
            return pd.read_csv(file.file)
        elif file.filename.endswith(('.xls', '.xlsx')):
            file.file.seek(0)  # Ensure the file pointer is at the beginning
            return pd.read_excel(file.file.read())
        else:
            raise ValueError("Unsupported file format. Please provide a CSV or Excel file.")
    else:
        raise ValueError("Unsupported input type. Please provide a file path or an uploaded file object.")

        
# Function to parse dates
def parse_mixed_dates(date_str):
    try:
        # Attempt to parse the date string using dateutil.parser
        return parser.parse(date_str, fuzzy=True)
    except (parser.ParserError, TypeError, ValueError):
        return np.nan  # Return NaN if the date cannot be parsed

def data_to_date(data1, date_column, year = None):
    """
    Convert mixed-format dates in specified column to datetime and extract year.
    
    Parameters:
    data1 (pd.DataFrame): The updated(after dropping missing values & selecting cols) input DataFrame.
    date_column (str): The column containing mixed-format dates.

    Returns:
    dict: A dictionary with the updated shape of the DataFrame.
    pd.DataFrame: The cleaned DataFrame with datetime column converted and year extracted.
    """
    # Apply the parse_mixed_dates function to parse mixed-format dates
    if not date_column:
        raise ValueError("No datetime column selected in the previous step.")
    try:
        date_columns = [col for col in data1.columns if data1[col].dtype == 'datetime64[ns]']
        if not date_columns:
            raise ValueError("No datetime column selected in the previous step.")
        data1 = data1.drop(columns = date_columns, axis=1)
    except:
        pass
    
    if data1[date_column].dtype == 'datetime64[ns]':
        data1[f"{date_column}_Year"] = data1[date_column].dt.year
    else:
        data1[date_column] = data1[date_column].apply(parse_mixed_dates)
        # Convert parsed dates to datetime
        data1[date_column] = pd.to_datetime(data1[date_column], errors="coerce")
        # Extract year and create a new column
        data1[f"{date_column}_Year"] = data1[date_column].dt.year
    
    # Drop the original datetime column
    data1.drop(date_column, axis=1, inplace=True)
    
        # Check if the specified year exists in the filtered DataFrame
    if not data1.empty and year not in data1[f"{date_column}_Year"].values:
        raise ValueError(f"Year {year} does not exist in the dataset.")
    
    # If year is specified, filter the DataFrame based on the newly generated year column
    if year is not None and f"{date_column}_Year" in data1.columns:
        data1 = data1[data1[f"{date_column}_Year"] == year]
    
    # Prepare the shape information as a dictionary
    updated_shape = {
        'rows': data1.shape[0],
        'columns': data1.shape[1]
    }
    
    return json.dumps(updated_shape), data1.to_json()

def summarize_df(df):
    """
    Gives the summary DataFrame including information about missing values, unique values & data type.

    Parameters:
        df (pd.DataFrame): The input DataFrame.

    Returns:
        table: A dataframe of column names that has their summary.
    """

    try:
        dtypes = df.dtypes  # Get data types
        non_null_counts = df.notnull().sum()  # Get non-null counts
        total_counts = len(df)  # Get total counts
        unique_counts = df.nunique()  # Get unique value counts
        missing_values = total_counts - non_null_counts  # Get missing values counts

        # Combine all data into a summary DataFrame
        summary = pd.DataFrame({
            'Data Type': dtypes,
            'Non-Null Count': non_null_counts,
            'Missing Values': missing_values,
            'Unique Values': unique_counts
        })
        return summary
    except KeyError as e:
        print(f"KeyError: {e}")
        print("Available columns:", df.columns)
        return pd.DataFrame()   

def set_properties(df, rprt):
    rprt.set_properties(headers=list(df.columns))
    return rprt

class DataInfoProcessor(DoorstepProcessor):
    preset = 'tabular'
    code = 'crimson-data-info:1'
    description = _("Crimson Data Info")

    def get_workflow(self, filename, metadata={}):
        workflow = {
            'load-csv': (pd.read_csv, filename),
            'step-A': (data_info, 'load-csv', self.make_report()),
            'step-B': (detect_date_columns, 'load-csv', self.make_report()),
            'condense': (workflow_condense, 'step-A', 'step-B'),
            'output': (set_properties, 'load-csv', 'condense')
        }
        return workflow

def workflow_condense(base, *args):
    return combine_reports(*args, base=base)

processor = DataInfoProcessor


if __name__ == "__main__":
    argv = sys.argv
    processor = DataInfoProcessor()
    workflow = processor.build_workflow(argv[1])
    print(get(workflow, 'output'))


