from optimizers.utils import *


def get_assets_ids(date):
    cols = ["columns=ASSET_DATABASE_ID", "columns=LABEL",
            "columns=TYPE", "columns=LAST_CLOSE_VALUE_IN_CURR",
            "columns=CURRENCY", "columns=MIN_BUY_AMOUNT",
            "columns=asset_fund_info_decimalisation"]
    endpointApi = "asset?{}&date={}".format("&".join(cols), date)
    data = pd.read_json(api.get(endpointApi))
    assets = convert_type(data)
    assets = assets[(assets['LAST_CLOSE_VALUE_IN_CURR'].notna())
                    & (assets['TYPE'] != 'PORTFOLIO')].reset_index()
    assets['MIN_BUY_AMOUNT'] = assets['MIN_BUY_AMOUNT'].fillna(value=1)
    assets['asset_fund_info_decimalisation'] = assets['asset_fund_info_decimalisation'].fillna(
        value=0)
    return assets[['ASSET_DATABASE_ID', 'CURRENCY', 'MIN_BUY_AMOUNT', 'asset_fund_info_decimalisation', "TYPE", "LAST_CLOSE_VALUE_IN_CURR"]]


def get_type_table():
    try:
        type_table = pd.read_csv("type_table.csv", index_col=0)
        return type_table
    except FileNotFoundError:
        type_table = get_assets_ids(start_period)
        type_table[["ASSET_DATABASE_ID", "TYPE"]].to_csv("type_table.csv")
        return type_table[["ASSET_DATABASE_ID", "TYPE"]]


def get_price_table():
    try:
        type_table = pd.read_csv("price_table.csv", index_col=0)
        return type_table
    except FileNotFoundError:
        type_table = get_assets_ids(start_period)
        type_table = type_table[["ASSET_DATABASE_ID",
                                 "LAST_CLOSE_VALUE_IN_CURR", "CURRENCY"]]
        type_table["value"] = type_table["LAST_CLOSE_VALUE_IN_CURR"].astype(
            str).str.cat(type_table["CURRENCY"].tolist(), sep=' ')
        type_table["LAST_CLOSE_VALUE_IN_CURR"] = type_table["value"].apply(
            to_eur).astype(float)
        type_table[["ASSET_DATABASE_ID", "LAST_CLOSE_VALUE_IN_CURR"]].to_csv(
            "price_table.csv")
        return type_table[["ASSET_DATABASE_ID", "LAST_CLOSE_VALUE_IN_CURR"]]


def get_type(id_):
    type_table = get_type_table()
    return type_table[type_table['ASSET_DATABASE_ID'] == id_].values[0, 1]


def get_types(ids):
    type_table = get_type_table()
    return np.array([type_table[type_table['ASSET_DATABASE_ID'] == id_].values[0, 1] for id_ in ids])


def get_types_ids(ids, types):
    type_table = get_type_table()
    return [i for i, id_ in enumerate(ids) if type_table[type_table['ASSET_DATABASE_ID'] == id_].values[0, 1] in types]


def select_type(type_list):
    table_type = get_type_table()
    table_type = table_type[table_type.TYPE.isin(type_list)].ASSET_DATABASE_ID
    return table_type.values


def get_price(id_):
    price_table = get_price_table()
    return price_table[price_table['ASSET_DATABASE_ID'] == id_].values[0, 1]


def get_prices(ids):
    price_table = get_price_table()
    return np.array([price_table[price_table['ASSET_DATABASE_ID'] == id_].values[0, 1] for id_ in ids])


def get_quote(id_, start, end):
    data = api.get('asset/{}/quote?start_date={}&end_date={}'
                   .format(id_, start, end))
    return convert_type(pd.read_json(data))


def process_val(close, asset_currency, asset_min_buy, decimalisation):
    return pow(10, -decimalisation) * (asset_min_buy or 1) * to_eur(str(close) + ' ' + asset_currency)


def get_quote_matrixes(start, end):
    try:
        all_closes = pd.read_csv("all_closes.csv", index_col=0)
        all_returns = pd.read_csv("all_returns.csv", index_col=0)
        return (all_closes, all_returns)
    except FileNotFoundError:
        assets = get_assets_ids(start)
        cur = assets.values[0]
        all_assets = get_quote(cur[0], start, end)
        close_matrix = all_assets[['close']].set_index(all_assets.date)
        close_matrix['close'] = close_matrix['close'].apply(
            lambda x: process_val(x, cur[1], cur[2], cur[3]))
        close_matrix.columns = ['{}'.format(cur[0])]
        return_matrix = all_assets[['return']].set_index(all_assets.date)
        return_matrix.columns = ['{}'.format(cur[0])]
        for i in range(1, len(assets)):
            cur = assets.values[i]
            all_assets = get_quote(cur[0], start, end)
            if 'close' in all_assets:
                cur_close = all_assets[['close']].set_index(all_assets.date)
                cur_close['close'] = cur_close['close'].apply(
                    lambda x: process_val(x, cur[1], cur[2], cur[3]))
                cur_close.columns = ['{}'.format(cur[0])]
                close_matrix = pd.concat(
                    [close_matrix, cur_close], axis=1, sort=False)
            if 'return' in all_assets:
                cur_return = all_assets[['return']].set_index(all_assets.date)
                cur_return.columns = ['{}'.format(cur[0])]
                return_matrix = pd.concat(
                    [return_matrix, cur_return], axis=1, sort=False)

        all_closes = close_matrix.sort_index().fillna(method='pad')
        all_returns = return_matrix.sort_index().fillna(method='pad')
        all_closes.to_csv("all_closes.csv")
        all_returns.to_csv("all_returns.csv")
        return (all_closes, all_returns)
