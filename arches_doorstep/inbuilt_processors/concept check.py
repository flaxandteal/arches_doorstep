import pandas as pd
from difflib import get_close_matches
import logging
import sys
import numpy as np
import re
from requests import get
from scipy.stats import mode
from difflib import SequenceMatcher
from ltldoorstep.reports.report import Report
from ltldoorstep.processor import DoorstepProcessor
from ltldoorstep.reports.report import combine_reports
from gettext import gettext as _
from dateutil import parser
import pytest
import json
from uuid import UUID
#from arches_orm.adapter import context_free, get_adapter
#from arches_orm.utils import string_to_enum
#from arches_orm.errors import DescriptorsNotYetSet
import xml.etree.ElementTree as ET

pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)

# Function to parse XML file and extract data
def parse_xml_file(filename):
    try:
        # Parse the XML file
        tree = ET.parse(filename)
        root = tree.getroot()

        # Define namespace mapping
        namespaces = {
            'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
            'skos': 'http://www.w3.org/2004/02/skos/core#'
        }

        # Extract id and value from skos:prefLabel elements
        results = []
        for pref_label in root.findall('.//skos:prefLabel', namespaces):
            try:
                # Parse JSON content inside skos:prefLabel
                label_data = json.loads(pref_label.text)
                results.append({'id': label_data['id'], 'value': label_data['value']})
            except (json.JSONDecodeError, KeyError, TypeError):
                pass
        
        return results

    except ET.ParseError as e:
        print(f"Error parsing XML file: {e}")
        return []

def extract_xml(filename):
    extracted_data = parse_xml_file(filename)
    collection_value = []
    #collection_value = []
    for i in range(0,len(extracted_data)):
        collection_value.append(extracted_data[i]['value'])
    collections_df = [extracted_data]
    cols = [collection_value]
    return cols, collections_df

filename = "thesaurus.xml"  # Replace with XML file path
collections_df, col_df = extract_xml(filename)
column_name = 'Process'
collection_list = collections_df[0]


def filter_and_match_columns(data, rprt):
    max_words: int = 4
    threshold: float = 0.1
    m: int = 10
    """
    Filters columns from the input dataframe and matches them to the closest collections.

    Parameters:
        data (pd.DataFrame): The input dataframe.
        collections_df (pd.DataFrame): DataFrame with collection columns of vocabularies.
        max_words (int): Maximum number of words allowed in a cell for a column to be considered.
        threshold (float): The minimum percentage of valid cells that must meet the word condition to include the column.

    Returns:
        dict: Mapping of filtered column names to their closest collection matches.
    """
    def has_max_words(cell, max_words):
        """Checks if a cell has at most `max_words` words."""
        if isinstance(cell, str):
            return len(cell.split()) <= max_words
        return False

    # Step 1: Filter columns with at least `threshold` percentage of cells containing fewer than `max_words` words
    filtered_columns = []
    for col in data.columns:
        # Exclude entirely NaN columns
        if data[col].isna().all():
            continue
        
        # Count the number of valid cells (not NaN) with fewer than `max_words` words
        valid_cells_count = data[col].apply(lambda x: has_max_words(x, max_words)).sum()
        total_cells = data[col].notna().sum()

        # If 90% of the valid (non-NaN) cells satisfy the word condition, include the column
        if total_cells > 0 and valid_cells_count / total_cells >= threshold:
            filtered_columns.append(col)

    #print(filtered_columns)
    
    # Flatten all collections into a single list for matching
    #all_collections = collections_df.values.flatten().tolist()
    #print(collections_df)
    
   # Step 2: Perform fuzzy matching for each filtered column with each collection in collections_df
    match_results = {}
    for col in filtered_columns:
        # Combine all entries in the column into a list
        col_entries = data[col].dropna().tolist()

        # Calculate fuzzy match percentage for each collection in collections_df
        col_results = {}
        for idx, collection in enumerate(collections_df):
            # Flatten the collection list into a single string for matching
            collection_flat = collection
            #print(collection_flat)
            
            # Count how many words from the column have a close match in the collection
            match_count = 0
            for word in col_entries:
                close_matches = get_close_matches(word, collection_flat, n=1, cutoff=0.5)  # Adjust cutoff as needed
                if close_matches:
                    match_count += 1

            # Calculate the match percentage
            match_percentage = (match_count / len(col_entries)) * 100 if len(col_entries) > 0 else 0
            if match_percentage >= m:
                col_results[f"col {col} has {match_percentage:.0f}% fuzzy match with collection_df[{idx}]"] = match_percentage

        if col_results:  # Only add columns with valid matches (60% or above)
            match_results[col] = col_results
    
    rprt.add_issue(
        logging.INFO,
        'mapping-summary',
        "Ideal Match summary",
        error_data=match_results
    )
    return rprt
    

def fuzzy_match_percentage(rprt, entry: str, collection_list: list):
    """
    Calculates the fuzzy match percentage of an entry against all entries in the collection list using SequenceMatcher.
    
    Parameters:
        entry (str): The string entry to match.
        collection_list (list): A list of strings to compare the entry against.
    
    Returns:
        tuple: The closest match from the collection list and the match percentage.
    """
    best_match = None
    highest_percentage = 0
    
    # Iterate through the collection list to find the best match
    for item in collection_list:
        match_ratio = SequenceMatcher(None, entry, item).ratio()
        match_percentage = match_ratio * 100
        
        # Keep track of the highest match percentage
        if match_percentage > highest_percentage:
            best_match = item
            highest_percentage = match_percentage
    
    return best_match, highest_percentage

# Function to add a new column with matched IDs to a DataFrame
def add_closest_match_ids(rprt, df, column_name, reference_list):
    # Flatten the reference list to a dictionary for quick lookup
    reference_dict = {item['value']: item['id'] for sublist in reference_list for item in sublist}

    def get_id(value):
        if value == "No close match found":
            return None
        return reference_dict.get(value)

    df['Closest Match ID'] = df[column_name].apply(get_id)
    return df


def match_column_entries_to_collection(data, rprt):
    cutoff: float = 70.0
    """
    For each entry in a column of the dataframe, checks if it has a fuzzy match with any entry in the collection list.
    Creates a new dataframe with the original entry, the closest match, and the match percentage.

    Parameters:
        data (pd.DataFrame): The input dataframe.
        column_name (str): The name of the column to check.
        collection_list (list): A list of words or phrases to compare against.
        cutoff (float): The minimum similarity ratio to consider a fuzzy match (default is 60%).

    Returns:
        pd.DataFrame: A new dataframe with the original entry, closest match, and match percentage.
    """
    match_results = []
    
    for entry in data[column_name]:  # Iterate through each entry in the specified column
        closest_match, match_percentage = fuzzy_match_percentage(rprt, entry, collection_list)
        
        if match_percentage >= cutoff:
            match_results.append([entry, closest_match, round(match_percentage, 2)])
        else:
            match_results.append([entry, "No close match found", None])

    # Convert the match results into a DataFrame
    result_df = pd.DataFrame(match_results, columns=["Original Entry", "Closest Match", "Match Percentage"])
    
    result__df = add_closest_match_ids(rprt, result_df, "Closest Match", col_df)
    
    rprt.add_issue(
        logging.INFO,
        'mapping-concept-summary',
        "Ideal Concept summary",
        error_data=result__df.to_json()
    )
    return rprt


def set_properties(df, rprt):
    rprt.set_properties(headers=list(df.columns))
    return rprt

class MappingInfoProcessor(DoorstepProcessor):
    preset = 'tabular'
    code = 'crimson-concept-info:1'
    description = _("Crimson Mapping Info")
    #description = "Crimson Mapping Info"

    def get_workflow(self, filename, metadata={}):
        workflow = {
            'load-csv': (pd.read_csv, filename),
            'step-A': (filter_and_match_columns, 'load-csv', self.make_report()),
            'step-B': (match_column_entries_to_collection, 'load-csv', self.make_report()),
            'condense': (workflow_condense, 'step-A', 'step-B'),
            'output': (set_properties, 'load-csv', 'condense')
        }
        return workflow

def workflow_condense(base, *args):
    return combine_reports(*args, base=base)

processor = MappingInfoProcessor



if __name__ == "__main__":
    argv = sys.argv
    processor = MappingInfoProcessor()
    workflow = processor.build_workflow(argv[1])
    print(get(workflow, 'output'))


