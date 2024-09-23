from cit_sci_client import CitSciClient
from cit_sci_processor import CitSciProcessor
import sys, argparse

parser = argparse.ArgumentParser()
parser.add_argument('project_id', type=str, help='CitSci project GUID')
parser.add_argument('project_slug', type=str, help='Descriptive project slug. Will be used to name tables and feature classes. Example: front_range_pika_project')

# get project details from arguments 
args = parser.parse_args()
project_id = args.project_id
project_slug = args.project_slug

client = CitSciClient()
processor = CitSciProcessor()

# create the project in the control table 
processor.create_project(project_id, project_slug)

# download initial set of project data and store in sql 
observation_data_file = client.save_observation_data(project_id=project_id, project_slug=project_slug)
processor.to_sql(file_name=observation_data_file, table_name=project_slug)