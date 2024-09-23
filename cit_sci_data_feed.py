from cit_sci_client import CitSciClient
from cit_sci_processor import CitSciProcessor
import logging, sys, argparse, cit_sci_utilities, datetime, os, traceback

parser = argparse.ArgumentParser()
parser.add_argument('internal_id', type=str, help='Internal CitSci project ID from the project_control table')

project_slug = ''

try:
    # get project details from arguments 
    args = parser.parse_args()
    internal_id = args.internal_id

    client = CitSciClient()
    processor = CitSciProcessor()

    # get project data using the internal id; result will be in this format: ('8b4da44d-f3b1-457d-99be-9f15b3bd5618', 'front_range_pika_project', 40804)
    project_data = processor.get_project_data(internal_id)

    if project_data == None:
        raise Exception('Could not find project data for internal_id = {id}'.format(id=internal_id))

    project_id = project_data[0]
    project_slug = project_data[1]

    # verify project data
    if project_id == '' or project_id == None:
        raise Exception('Empty or NULL project_id for internal_id = {id} in project_control'.format(id=internal_id))
    if project_slug == '' or project_slug == None:
        raise Exception('Empty or NULL project_slug for internal_id = {id} in project_control'.format(id=internal_id))

    # create log dir if it doesn't exist
    if not os.path.exists(r'logs'):
        os.mkdir(r'logs')

    # set up logging
    formatted_date = datetime.datetime.now().strftime('%m.%d.%Y_%H.%M.%S')
    log_file = os.path.join('logs', '{prefix}_{formatted_date}.log'.format(formatted_date=formatted_date, prefix=project_slug))
    logging.basicConfig(
        format='%(asctime)s - %(levelname)s - %(message)s',
        level=logging.INFO,
        datefmt='%m-%d-%Y %H:%M:%S',
        filename=log_file,
        filemode='w'
    )

    # download and save the observation data to a file
    logging.info('Downloading and saving data for {name}...'.format(name=project_slug))
    observation_data_file = client.save_observation_data(project_id=project_id, project_slug=project_slug)
    
    # read observation data file and store in sql server; this will also trigger some light data processing
    logging.info('Storing data in {name} table in SQL...'.format(name=project_slug))
    processor.to_sql(file_name=observation_data_file, table_name=project_slug)
    
    logging.info('{name} data refreshed! Terminating script.'.format(name=project_slug))

except Exception as e:
    error_message = traceback.format_exc()
    print(error_message)
    logging.error(error_message)

finally:
    # clean up old log files 
    if project_slug != None and project_slug != '':
        cit_sci_utilities.remove_items_last_mod_date('logs', project_slug, 14)
