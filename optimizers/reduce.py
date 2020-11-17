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
    return assets[['ASSET_DATABASE_ID', 'LABEL', 'CURRENCY', 'MIN_BUY_AMOUNT', 'asset_fund_info_decimalisation', "TYPE"]]


def process_val(close, asset_currency, asset_min_buy, decimalisation):
    return pow(10, -decimalisation) * (asset_min_buy or 1) * to_eur(str(close) + ' ' + asset_currency)


def get_all_assets_quote(assets, start, end, stock):
    asset_id = assets['ASSET_DATABASE_ID'][0]
#     asset_name = assets['LABEL'][0]
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
        total_quote = get_all_assets_quote(ids, start, end, stock)
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
