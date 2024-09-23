import pyodbc, os, pandas as pd, numpy as np, sqlalchemy, urllib
from datetime import date

class CitSciProcessor:
    # constructor
    def __new__(cls, *args, **kwargs):
        return super().__new__(cls)

    def __init__(self):
        self.driver = 'ODBC Driver 17 for SQL Server'
        self.test_db_server = 'TEST DATABASE SERVER'
        self.database = 'CitSci'

    def __repr__(self):
        return '{type}'.format(type=type(self).__name__)

    def get_project_data(self, internal_id):
        conn = pyodbc.connect('DRIVER={driver};SERVER={server};DATABASE={database};Trusted_Connection=yes'.format(driver=self.driver, server=self.test_db_server, database=self.database))
        cursor = conn.cursor()
        try:
            query = "EXEC [dbo].[sp_Get_Project] @internalID = ?"
            params = (internal_id)
            cursor.execute( query, params )
            return cursor.fetchone()
        finally: 
            conn.close()

    def create_project(self, project_id, project_slug):
        conn = pyodbc.connect('DRIVER={driver};SERVER={server};DATABASE={database};Trusted_Connection=yes'.format(driver=self.driver, server=self.test_db_server, database=self.database))
        cursor = conn.cursor()
        try:
            query = "EXEC [dbo].[sp_Create_Project] @projectID = ?, @projectSlug = ?"
            params = (project_id, project_slug)
            cursor.execute( query, params )
            conn.commit()
        finally: 
            conn.close()

    def to_sql(self, file_name, table_name):
        # read jsonlines file and convert to data frame
        df = pd.DataFrame()
        reader = pd.read_json(file_name, lines=True, chunksize=10)
        for chunk in reader:
            df = pd.concat([df, chunk], ignore_index=True)

        #df = df.join(pd.json_normalize(df["records"])).drop(["records"], axis=1)
        df["observedAt"] = pd.to_datetime(df["observedAt"], infer_datetime_format=True)
        df["createdAt"] = pd.to_datetime(df["createdAt"], infer_datetime_format=True)
        df["updatedAt"] = pd.to_datetime(df["updatedAt"], infer_datetime_format=True)

        dtypes = {
            "observedAt": sqlalchemy.types.DateTime,
            "createdAt": sqlalchemy.types.DateTime,
            "updatedAt": sqlalchemy.types.DateTime
        }

        # drop the table
        self._drop_table(table_name)

        connection_string = urllib.parse.quote_plus('DRIVER={driver};SERVER={server};DATABASE={database};Trusted_Connection=yes'.format(driver=self.driver, server=self.test_db_server, database=self.database))
        engine = sqlalchemy.create_engine('mssql+pyodbc:///?odbc_connect={connection_string}'.format(connection_string=connection_string), fast_executemany=True)
        with engine.connect() as connection:
            df.to_sql(name=table_name, con=connection, if_exists='replace', schema='dbo', index=False, dtype=dtypes, chunksize=1000)

        # add and set the shape field 
        self._process_data(table_name)

    def _drop_table(self, table_name):
        conn = pyodbc.connect('DRIVER={driver};SERVER={server};DATABASE={database};Trusted_Connection=yes'.format(driver=self.driver, server=self.test_db_server, database=self.database))
        cursor = conn.cursor()
        try:
            query = "EXEC [dbo].[sp_Drop_Table] @tableName = ?"
            params = (table_name)
            cursor.execute( query, params )
            conn.commit()
        finally: 
            conn.close()

    def _process_data(self, table_name):
        conn = pyodbc.connect('DRIVER={driver};SERVER={server};DATABASE={database};Trusted_Connection=yes'.format(driver=self.driver, server=self.test_db_server, database=self.database))
        cursor = conn.cursor()
        try:
            query = "EXEC [dbo].[sp_Process_Data] @tableName = ?"
            params = (table_name)
            cursor.execute( query, params )
            conn.commit()
        finally: 
            conn.close()