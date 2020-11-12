from config import api_url, api_user_auth, api_pass_auth
import requests
import json

class DolphinApi:
    def __init__(self):
        self.url = api_url
        self.auth = (api_user_auth, api_pass_auth)

    def get(self, endpointApi, date=None, full_response=False, columns=list()):
        payload = {'date': date, 'fullResponse': full_response}
        res = requests.get(self.url + endpointApi,
                           params=payload,
                           auth=self.auth,
                           verify=False)
        return res.content.decode('utf-8')

    def put(self, endpointApi, content):
        res = requests.put(url=self.url + endpointApi,
                          data=json.dumps(content),
                          auth=self.auth,
                          headers = {"content-type": "application/json"},
                          verify=False)
        return res.content.decode('utf-8')

    def post(self, endpointApi, content):
        res = requests.post(url=self.url + endpointApi,
                    data=json.dumps(content),
                    auth=self.auth,
                    headers = {"content-type": "application/json"},
                    verify=False)
        return res.content.decode('utf-8')