from .config import api_url, api_user_auth, api_pass_auth, portofolio_label
import requests
import json
import pandas as pd

class DolphinApi:
    def __init__(self):
        self.url = api_url
        self.auth = (api_user_auth, api_pass_auth)
        self.portofolio_label = portofolio_label
        try:
            self.currency_table = pd.read_csv("currency_table.csv", index_col=0)
        except FileNotFoundError: 
            self.currency_table = self.__get_currency_rate__()
            self.currency_table.to_csv("currency_table.csv")
        try:
            self.operations_table = pd.read_csv("operations_table.csv", index_col=0)
        except FileNotFoundError: 
            self.operations_table = self.__get_operations_table__()
            self.operations_table.to_csv("operations_table.csv")

    def get(self, endpointApi, date=None, full_response=False):
        payload = {'date': date, 'fullResponse': full_response}
        res = requests.get(self.url + endpointApi,
                           params=payload,
                           auth=self.auth)
        return res.content.decode('utf-8')

    def put(self, endpointApi, content):
        res = requests.put(url=self.url + endpointApi,
                          data=json.dumps(content),
                          auth=self.auth,
                          headers = {"content-type": "application/json"})
        return res.content.decode('utf-8')

    def post(self, endpointApi, content):
        res = requests.post(url=self.url + endpointApi,
                    data=json.dumps(content),
                    auth=self.auth,
                    headers = {"content-type": "application/json"})
        return res.content.decode('utf-8')

    def __get_currency_rate__(self):
        d = []
        arr = json.loads(self.get('currency'))
        for currency in arr:
            currency_id = currency.get('id')
            rate = self.get('currency/rate/{}/to/EUR'.format(currency_id))
            if len(rate) != 0:
                d.append([currency_id, (json.loads(rate)['rate']['value']).replace(',', '.')])
        return pd.DataFrame(d, columns=['currency', 'rate'])

    def __get_operations_table__(self):
        data = self.get('ratio')
        return pd.read_json(data)

api = DolphinApi()