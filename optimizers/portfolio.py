from optimizers.utils import *


def get_portfolio(id_):
    data = api.get('portfolio/{}/dyn_amount_compo'.format(id_))
    portfolio = pd.read_json(data)
    return portfolio


def get_portfolio_IDs():
    cols = ["columns=TYPE", "columns=ASSET_DATABASE_ID", "columns=LABEL"]
    endpointApi = "asset?{}&date={}".format("&".join(cols), start_period)
    data = pd.read_json(api.get(endpointApi))
    assets = convert_type(data)
    assets = assets[(assets['TYPE'] == 'PORTFOLIO')].reset_index()
    return assets
    portfolio_id = assets.loc[
        (assets['TYPE'] == 'PORTFOLIO') &
        (assets['LABEL'] == api.portofolio_label)]['ASSET_DATABASE_ID'].values[0]
    return int(portfolio_id)


def get_epita_portfolio_id():
    df_IDs = get_portfolio_IDs()
    return int(df_IDs.loc[df_IDs['LABEL'] == 'EPITA_PTF_4']['ASSET_DATABASE_ID'])


def get_epita_portfolio():
    epita_portfolio_id = get_epita_portfolio_id()
    return get_portfolio(epita_portfolio_id)


def get_assets_portfolio(portfolio, date):
    if date not in portfolio['values']:
        return np.NaN
    return portfolio['values'][date]


def put_portfolio(portfolio_id, df_portfolio, assets):
    label = df_portfolio['label'][0]
    currency = df_portfolio['currency'][0]
    type_ = df_portfolio['type'][0]
    date = '2016-06-01'
    form = '{{"asset":{{"asset": {}, "quantity": {}}}}},'
    assets = ''.join([form.format(int(assets.iloc[i, 0]),
                                  int(assets.iloc[i, 1]))
                      for i in range(len(assets))])[:-1]
    form = '{{"label": "{}", "currency": {{"code": "{}"}}, "type": "{}", "values": {{"{}": [{}]}}}}'
    res = form.format(label, currency, type_, date, assets)
    form = 'portfolio/{}/dyn_amount_compo'
    api.put(form.format(portfolio_id), json.loads(res))
