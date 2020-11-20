from DolphinApi.DolphinApi import DolphinApi, api
from DolphinApi.config import *

from portfolio import *
from tables import *

from datetime import datetime
import pandas as pd
import numpy as np
import json


def to_eur(src_value):
    value, src_currency = src_value.split(' ')
    rate = api.currency_table[api.currency_table['currency']
                              == src_currency]['rate'].values[0]
    return float(value.replace(',', '.')) * float(rate)


def convert_type(df):
    for col in df.columns:
        convert_values = []
        for elt in df[col]:
            if elt is np.nan:
                convert_values.append(np.nan)
                continue
            elt_type, elt_value = elt['type'], elt['value']
            elif elt_type in ['asset', 'int32', 'int64']:
                elt_value = int(elt_value)
            elif elt_type in ['double', 'percent']:
                elt_value = float(elt_value.replace(',', '.'))
            elif elt_type == 'date':
                elt_value = datetime.strptime(elt_value, '%Y-%m-%d').date()
            if elt_type == 'currency_value':
                elt_value = to_eur(elt_value)
            elif elt_type == 'boolean':
                elt_value = json.loads(elt_value)
            convert_values.append(elt_value)
        df[col] = convert_values
    return df


def get_asset_full_info(id_):
    data = api.get('asset/')
    asset = convert_type(pd.read_json(data))
    asset[asset['ASSET_DATABASE_ID'] == id_].to_csv("test.csv")
    return asset[asset['ASSET_DATABASE_ID'] == id_]
