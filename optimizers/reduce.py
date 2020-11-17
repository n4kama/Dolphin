from .utils import *
import pandas as pd


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
    return assets[['ASSET_DATABASE_ID', 'CURRENCY', 'MIN_BUY_AMOUNT', 'asset_fund_info_decimalisation', "TYPE"]]


def process_val(close, asset_currency, asset_min_buy, decimalisation):
    return pow(10, -decimalisation) * (asset_min_buy or 1) * to_eur(str(close) + ' ' + asset_currency)


def get_all_assets_quote(assets, start, end):
    asset_id = assets['ASSET_DATABASE_ID'][0]
    asset_currency = assets['CURRENCY'][0]
    asset_min_buy = assets['MIN_BUY_AMOUNT'][0]
    asset_decima = assets['asset_fund_info_decimalisation'][0]
    all_assets = get_quote(asset_id, start, end)
    all_assets = all_assets[['close']].set_index(all_assets.date)
    all_assets['close'] = all_assets['close'].apply(
        lambda x: process_val(x, asset_currency, asset_min_buy, asset_decima))
    all_assets.columns = ['{}'.format(asset_id)]
    for i in range(1, len(assets)):
        if (stock and assets['ASSET_DATABASE_ID'][i] != "STOCK"):
            continue
        if (not stock and assets['ASSET_DATABASE_ID'][i] == "STOCK"):
            continue
        asset_id = assets['ASSET_DATABASE_ID'][i]
#         asset_name = assets['LABEL'][i]
        asset_currency = assets['CURRENCY'][i]
        asset_min_buy = assets['MIN_BUY_AMOUNT'][i]
        asset_decima = assets['asset_fund_info_decimalisation'][i]
        asset_quote = get_quote(asset_id, start, end)
        if 'close' in asset_quote:
            asset_quote = asset_quote[['close']].set_index(asset_quote.date)
            asset_quote['close'] = asset_quote['close'].apply(
                lambda x: process_val(x, asset_currency, asset_min_buy, asset_decima))
            asset_quote.columns = ['{}'.format(asset_id)]
            all_assets = pd.concat(
                [all_assets, asset_quote], axis=1, sort=False)
    return all_assets.fillna(method='pad')


def choose_from(start, end, nb, stock):
    ids = get_assets_ids(start)
    try:
        total_quote = pd.read_csv("all_quotes.csv", index_col=0)
    except FileNotFoundError:
        total_quote = get_all_assets_quote(ids, start, end)
        total_quote.to_csv("all_quotes.csv")
    best_ids = []
    # corr_table = total_quote.corr()
    # corr_table['asset_id_1'] = corr_table.index
    # corr_table = corr_table.melt(
    #     id_vars='asset_id_1', var_name="asset_id_2").reset_index(drop=True)
    # corr_table = corr_table[corr_table['asset_id_1']
    #                         < corr_table['asset_id_2']].dropna()
    # corr_table['abs_value'] = np.abs(corr_table['value'])
    # corr_low_to_high = corr_table.sort_values("abs_value", ascending=True)
    # for index, row in corr_low_to_high.iterrows():
    #     asset_id_1 = row['asset_id_1']
    #     asset_id_2 = row['asset_id_2']
    #     if not int(asset_id_1) in best_ids:
    #         best_ids.append(int(asset_id_1))
    #     if len(best_ids) == nb:
    #         break
    #     if not int(asset_id_2) in best_ids:
    #         best_ids.append(int(asset_id_2))
    #     if len(best_ids) == nb:
    #         break
    aaa = ids['ASSET_DATABASE_ID'].to_list()
    df = post_operations([12], aaa, start, end)
    df = df.sort_values("Sharpe", ascending=False)
    best_ids = df.reset_index()['index'][:nb].to_list()

    return best_ids


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
        print(close_matrix)
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
