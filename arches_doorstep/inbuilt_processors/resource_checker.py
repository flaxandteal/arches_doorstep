import ast
from rapidfuzz import process
import pandas as pd
from difflib import get_close_matches
import logging
import sys
from requests import get
from difflib import SequenceMatcher
from ltldoorstep.processor import DoorstepProcessor
from ltldoorstep.reports.report import combine_reports
from django.utils.translation import gettext as _
#from arches.app.models import models
import json
#from arches_orm.adapter import context_free, get_adapter
#from arches_orm.utils import string_to_enum
#from arches_orm.errors import DescriptorsNotYetSet
import xml.etree.ElementTree as ET
import os

pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)


def pull_mapping_resource(data):
    # Extract the graph name
    graph_name = data.get("graph", {}).get("name", "")

    # Extract field and node names for mappings with datatype "concept" or "concept-list"
    field_names = [
        mapping.get("field")
        for mapping in data.get("mapping", [])
        if mapping.get("datatype") in ["resource", "resource-instance"]
    ]

    node_names = [
        mapping.get("node")
        for mapping in data.get("mapping", [])
        if mapping.get("datatype") in ["resource", "resource-instance"]
    ]
        # Print the output
    return graph_name,field_names,node_names

# Function to convert string entries into Python sets
def convert_to_json(data):
    result = []
    for sublist in data:
        converted_sublist = [ast.literal_eval(entry.strip(',')) for entry in sublist]
        result.append(converted_sublist)
    return result

def initialise_mapping(mapping):
    global graph_name, field_names, node_names
    graph_name,field_names,node_names = pull_mapping_resource(mapping)
#graph_name,field_names,node_names


#data = pd.read_csv('data-extracts-objects.csv')

"""
existing_resources = []
for i in range(0, len(node_names)):
    loaded_list = [node_names[i]]   #replace code here to get the list for entries in resource instance
    existing_resources.append(loaded_list)
"""


# Loaded lists in existing_resources would look something like this ie {Resource Name, uuid}
current_dir = os.path.dirname(__file__)
csv_file_path = os.path.join(current_dir, 'Resource-list-sample.csv')
resource_sample = pd.read_csv(csv_file_path)
notna_people = resource_sample['People'].dropna().tolist()
notna_area = resource_sample['Area'].dropna().tolist()
existing_resources = [notna_area, notna_people, notna_people, notna_people]
existing_resources = convert_to_json(existing_resources) # Convert data

#len(existing_resources)
#len(existing_resources[0]), len(existing_resources[1]), len(existing_resources[2]), len(existing_resources[3])
#existing_resources[0][0]


# Function to extract names (first part) from the sets
def extract_names(rprt, resource_options):
    return [{"name": list(option - {uuid})[0], "uuid": uuid}
            for option in resource_options for uuid in option if '-' in uuid]


# Function to perform fuzzy matching for a single column
def fuzzy_match_column(rprt, data_column, resource_options, column_index):
    # Extract names and UUIDs from resource options
    resources = extract_names(rprt, resource_options)
    names = [res["name"] for res in resources]
    
    # Perform fuzzy matching
    results = []
    for index, entry in enumerate(data_column):
        if type(entry) != str:
            continue 
        match_data = process.extractOne(entry, names)  # Returns a tuple (match, score, index)
        if match_data:
            match, score, index = match_data
            matched_resource = resources[index]
            results.append((entry, match, score, matched_resource["uuid"], index, column_index))
        else:
            results.append((entry, None, 0, None, index, column_index))  # No match found
    # Convert results to a DataFrame
    return pd.DataFrame(results, columns=["Entry", "Closest Match", "Score", "UUID", "Row Index", "Column Index"])

def resource_check(data, rprt):
    # Process each column in field_names
    output_dataframes = []
    for idx, field in enumerate(field_names):
        resource_options = existing_resources[idx]
        result_df = fuzzy_match_column(rprt, data[field], resource_options, idx)
        # Extract columns from result__df
        original_entries = result_df["Entry"].tolist()
        closest_matches = result_df["Closest Match"].tolist()
        match_percentage = result_df["Score"].tolist()
        closest_match_id = result_df["UUID"].tolist() 
        row_indices = result_df["Row Index"].tolist()
        column_indices = result_df["Column Index"].tolist()

        # Merge columns into a list of dictionaries
        merged_results = [
            {
                "original_entry": o,
                "closest_match": c,
                "match_percentage": p,
                "closest_match_id": i,
                "row_index": r + 1,
                "column_index": col + 1
            }
            for o, c, p, i, r, col in zip(original_entries, closest_matches, match_percentage, closest_match_id, row_indices, column_indices)
        ]
        #output_dataframes.append(merged_results)
        
        rprt.add_issue(
            logging.INFO,
            'mapping-resource-summary',
             _("These results are for {} column").format(field_names[idx]),
            error_data=json.dumps(merged_results, default=str)
        )
        
    return rprt
    #return json.dumps(output_dataframes)


def set_properties(df, rprt):
    rprt.set_properties(headers=list(df.columns))
    return rprt

class MappingResourceProcessor(DoorstepProcessor):
    preset = 'tabular'
    code = 'crimson-resource-info:1'
    description = _("Crimson Resource Mapping Info")
    #description = "Crimson Resource Mapping Info"

    def get_workflow(self, filename, context, metadata={}):
        mapping = json.loads(context.settings['mapping'])
        workflow = {
            'load-csv': (pd.read_csv, filename),
            'load-mapping': (initialise_mapping(mapping)),
            'step-A': (resource_check, 'load-csv', self.make_report()),
            'condense': (workflow_condense, 'step-A'),
            'output': (set_properties, 'load-csv', 'condense')
        }
        return workflow

def workflow_condense(base, *args):
    return combine_reports(*args, base=base)

processor = MappingResourceProcessor


if __name__ == "__main__":
    argv = sys.argv
    processor = MappingResourceProcessor()
    workflow = processor.build_workflow(argv[1])
    print(get(workflow, 'output'))

