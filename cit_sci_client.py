import requests, json, os, jsonlines
import regex as re
from requests.packages import urllib3
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from http.client import HTTPConnection

# TODO: eventually, CitSci will offer a bulk download for observation details, so we'll need to add a method to call that endpoint

class InvalidToken(Exception):
    pass

class CitSciClient: 
    # constructor
    def __new__(cls, *args, **kwargs):
        return super().__new__(cls)

    def __init__(self):
        #HTTPConnection.debuglevel = 1

        self.http = requests.Session()
        self.http.mount("https://", self.adapter)
        self.http.mount("http://", self.adapter)
        self.http.headers.update(self.headers)
        self.authenticate()

    def __repr__(self):
        return '{type}'.format(type=type(self).__name__)

    def __del__(self):
        self.http.close()
    
    # instance variables 
    access_token = ''

    refresh_token = ''

    base_url = 'https://api.citsci.org'

    retry_strategy = Retry(
        total=3,
        status_forcelist=[429, 500, 502, 503, 504],
        method_whitelist=["HEAD", "GET", "OPTIONS"],
        backoff_factor=2
    )
    
    adapter = HTTPAdapter(max_retries=retry_strategy)

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.60 Safari/537.36",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Content-Type": "application/json",
        "Upgrade-Insecure-Requests": "1",
        "Accept": "*/*",
    }

    def _call(self, endpoint, method, payload=None):
        '''
        Calls the API with just the given parameters. used exclusively by _call_api()
        :param endpoint: string of the endpoint being called.
        :param method: HTTP method (GET, POST, PUT, DELETE)
        :param payload: request payload (None by default)
        :return: JSON from response
        '''
        url = self.base_url + endpoint
        response = self.http.request(method=method, url=url, data=payload)
        if response.status_code == 401:
            raise InvalidToken('Access Token is Expired')
        return response.json()

    def _call_api(self, endpoint, method, payload=None):
        '''
        Utility function for calling API. This will be used by other functions in the class. 
        Handles token refresh. It attempts the token refresh just once.
        :param endpoint: string of the endpoint being called.
        :param method: HTTP method (GET, POST, PUT, DELETE)
        :param payload: request payload (None by default)
        :return: JSON from response
        '''
        try:
            return self._call(endpoint, method, payload)
        except InvalidToken:
            self.refresh_access_token()
            return self._call(endpoint)

    def authenticate(self): 
        '''
        Authenticates with the CitSci API. Sets the access_token and refresh_token
        '''
        url = '{base}/login'.format(base=self.base_url)
        payload = {"username": "USERNAME", "password": "PASSWORD"}
        response = self.http.post(url, data=json.dumps(payload))
        if (response.status_code == 200):
            response_data = response.json()
            self.access_token = response_data['token']
            self.refresh_token = response_data['refresh_token']
            
            # update http headers accordingly 
            self.http.headers.update({"Authorization": "Bearer {token}".format(token=self.access_token)})
        else:
            raise Exception("Could not authenticate. Response details: {response}".format(response=response))

    def refresh_access_token(self):
        '''
        Refreshes the access_token using the refresh_token
        '''
        if response.status_code == 401:
            url = '{base}/token/refresh'.format(base=self.base_url)
            payload = {"refresh_token": self.refresh_token}
            response = self.http.post(url, data=payload)
            if (response.status_code == 200):
                response_data = response.json()

                # save token data
                self.access_token = response_data['token']
                self.refresh_token = response_data['refresh_token']
                
                # update http header
                self.http.headers["Authorization"] = "Bearer {token}".format(token=self.access_token)
            else: 
                raise Exception("Could not refresh token. Response details: {response}".format(response=response))

    def save_observation_data(self, project_id, project_slug):
        '''
        Gets observation data (not records) and writes to a jsonlines file.
        Handles API pagination.
        :param project_id: unique CitSci project id (guid)
        :param project_slug: short project name used in the txt file name
        :return: Name of the txt file containing all of the observation ids
        '''
        if not os.path.exists(r'raw-data'):
            os.mkdir(r'raw-data')

        if os.path.exists(os.path.join(r'raw-data', '{slug}_observation_data.jsonl'.format(slug=project_slug))):
            os.remove(os.path.join(r'raw-data', '{slug}_observation_data.jsonl'.format(slug=project_slug)))

        endpoint = '/projects/{id}/observations'.format(base=self.base_url, id=project_id)

        all_pages_retrieved = False
        next_page = ''

        with jsonlines.open(os.path.join(r'raw-data', '{slug}_observation_data.jsonl'.format(slug=project_slug)), mode='a') as writer:
            while all_pages_retrieved == False:
                # make a request to get the observations
                if next_page != '':
                    endpoint = '{next}'.format(next=next_page)
                response = self._call_api(endpoint, 'GET')
                # get observation data from "hydra:member"
                if "hydra:member" in response:
                    for member in response["hydra:member"]:
                        # extract just the attributes we want 
                        data = {
                            "id": member["id"],
                            "observedAt": member["observedAt"],
                            "createdAt": member["createdAt"],
                            "updatedAt": member["updatedAt"],
                            "locationName": member["location"]["name"],
                            "latitude": member["location"]["latitude"],
                            "longitude": member["location"]["longitude"],
                            "url": 'https://citsci.org/observation/show/{id}'.format(id=member["id"])
                        }
                        writer.write(data)
                # check for next page 
                if "hydra:view" in response:
                    # check next page 
                    if "hydra:next" in response["hydra:view"]:
                        next_page = response["hydra:view"]["hydra:next"]
                    else:
                        all_pages_retrieved = True
        return os.path.join(r'raw-data', '{slug}_observation_data.jsonl'.format(slug=project_slug))

    def _format_column_name(self, name):
        # punctuation
        name = re.sub("[\?\'\,\;\:\.\(\)\/]", '', name)
        # ampersand
        name = re.sub('[\&]', 'and', name)
        # greater than, less than, greater than or equal to, less than or equal to 
        name = re.sub('(\>\/*\s*\=)', 'gtoe_', name)
        name = re.sub('(\<\/*\s*\=)', 'ltoe_', name)
        name = re.sub('(\<)', 'lt_', name)
        name = re.sub('(\>)', 'gt_', name)
        # digits+, e.g., 16+
        name = re.sub('(?<=(\d+))\+', ' plus', name)
        # percents
        name = re.sub('[\%]', 'pct', name)
        # micrograms
        name = name.replace('µ', 'mc')
        # ’ char
        name = name.replace('’', '')
        # standalone +
        name = name.replace('+', 'and')
        # separators
        name = re.sub('[\-\*\s]', '_', name)
        return name
