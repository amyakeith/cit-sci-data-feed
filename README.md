# CitSci Data Feed

## Overview

This repo contains scripts to collect data from [CitSci](https://citsci.org/) and store it the CARES system.

## Important assets 

### SQL

**CitSci database on TEST DATABASE SERVER**
- Stores raw CitSci project data. Each project gets its own table.
- The **PROJECT_CONTROL_TABLE** table contains important project configuration information used by the scripts.

## How to set up a new project data feed

Follow these steps to extract data for a new CitSci project and store it in the test database.

### 1. Run cit_sci_project_setup.py

- `cd` into the script directory
- Know your arguments
    - project_id: This is CitSci's GUID for a project. You can find it by making a request to the CitSci API and using the query string ?name={searchString}, where searchString contains a keyword. The API will return an array of projects and the project GUID will be stored in the "id" property

        For example, if you want to search for projects related to pikas, make a request to https://api.citsci.org/projects?name=pika
    - project_slug: This is a short but descriptive name for the CitSci project. This name will be used to define data tables and feature classes. Examples: front_range_pika_project and utah_water_watch. Avoid unusual characters and spaces.
- Run the script on the command line and pass in your arguments: `project_setup.py project_id project_slug` 

    Example: `python cit_sci_project_setup.py 8b4da44d-f3b1-457d-99be-9f15b3bd5618 front_range_pika_project`

### 2. Run cit_sci_data_feed.py with required argument

- Know your argument
    - internal_id: This is the id we use to identify a CitSci project. You can get it from **PROJECT_CONTROL_TABLE**
- Run this python command from the command line with your internal_id argument: `cit_sci_data_feed.py internal_id`
- Each time the script runs it will:
    - Write a log file to the `logs` folder, documenting execution steps and any errors.