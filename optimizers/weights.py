import numpy as np
import pandas as pd
from pyswarm import pso
import scipy.optimize as optimize

from DolphinApi.config import *
from optimizers.utils import *


def process_val_back(id_, w):
    cols = ["columns=ASSET_DATABASE_ID", "columns=LABEL",
            "columns=TYPE", "columns=LAST_CLOSE_VALUE_IN_CURR",
            "columns=CURRENCY", "columns=MIN_BUY_AMOUNT",
            "columns=asset_fund_info_decimalisation"]
    endpointApi = "asset?{}&date={}".format("&".join(cols), start_period)
    data = pd.read_json(api.get(endpointApi))
    assets = convert_type(data)
    assets = assets[(assets['LAST_CLOSE_VALUE_IN_CURR'].notna())
                    & (assets['TYPE'] != 'PORTFOLIO')].reset_index()
    assets['MIN_BUY_AMOUNT'] = assets['MIN_BUY_AMOUNT'].fillna(value=1)
    assets['asset_fund_info_decimalisation'] = assets['asset_fund_info_decimalisation'].fillna(
        value=0)
    assets = assets[['ASSET_DATABASE_ID', 'LABEL', 'CURRENCY',
                     'MIN_BUY_AMOUNT', 'asset_fund_info_decimalisation']]
    assets = assets[assets['ASSET_DATABASE_ID']= id_]
    return w / (asset_min_buy or 1)


def minimize_negative_sharpe(weights, asset_ids, portefolio_id, portefolio):
    """
    Minimize the negative sharpe on the entire portfolio

    Since optimize.minimize seeks to minimize, we return
    the negative of our portfolio sharpe (which we want to be big)
    """

    weights = np.array([process_val_back(asset_ids[i], weights[i]*100000)
                        for i in range(len(asset_ids))])

    # Update portfolio with new weights
    assets_dataframe = pd.DataFrame(
        data={'asset_id': asset_ids, 'quantities': weights})

    assets_dataframe['weighths']

    # Put portfolio
    put_portfolio(portefolio_id, portefolio, assets_dataframe)

    # must do at least once..
    post_operations([12], [portefolio_id], start_period, end_period)
    sharp = post_operations([12], [portefolio_id],
                            start_period, end_period).values[0, 0]

    print(sharp)
    return -sharp


def get_type(id_):
    data = api.get(
        'asset?columns=TYPE&columns=ASSET_DATABASE_ID&date={}'.format(start_period))
    asset = convert_type(pd.read_json(data))
    return asset[asset['ASSET_DATABASE_ID'] == id_].values[0, 0]


def is_fund_or_etf_or_index(x, asset_ids):
    res = 0
    for i, id_ in enumerate(asset_ids):
        res = x[i] if get_type(id_) != "stock" else 0
    return res


def rend_calc(asset_ids, x, i):
    rend_line = post_operations(
        [13], asset_ids, start_period, end_period).values[:, 0]
    return rend_line[i] * x[i] / np.sum(np.array(rend_line) * np.array(x))


def neo_opti_portfolio(asset_ids):
    """
    Optimize the number of each asserts in the portfolio

    The asserts themselves cannot be changed

    Parameters
    ----------  
    assets : array
        Assets id in the portfolio
    """

    portefolio_id = get_epita_portfolio_id()
    portefolio = get_epita_portfolio()
    nb_assets = len(asset_ids)
    weights = [1/nb_assets] * nb_assets
    print(asset_ids)

    constraints_list = [{'type': 'eq', 'fun': lambda x: np.sum(x) - 1},
                        {'type': 'eq', 'fun': lambda x: is_fund_or_etf_or_index(x, asset_ids) - 0.49}]
    inf_borne = [{'type': 'eq', 'fun': lambda x: rend_calc(
        asset_ids, x, i) - 0.1} for i in range(len(asset_ids))]
    constraints_list.append(inf_borne[0])
    sup_borne = [{'type': 'eq', 'fun': lambda x: 0.01 -
                  rend_calc(asset_ids, x, i)} for i in range(len(asset_ids))]
    constraints_list.append(sup_borne[0])
    constraints = tuple(constraints_list)

    bounds = tuple((0, 1) for x in range(nb_assets))

    optimal_sharpe = optimize.minimize(minimize_negative_sharpe,
                                       weights,
                                       (asset_ids, portefolio_id, portefolio),
                                       method='SLSQP',
                                       bounds=bounds,
                                       constraints=constraints)
    optimal_sharpe_arr = optimal_sharpe['x']
    print(f"[DEBUG] After optimization : {optimal_sharpe_arr}")
    print("sharp of portfolio =", post_operations(
        [12], [portefolio_id], start_period, end_period).values[0, 0])
    print("sharp of ref =", post_operations(
        [12], [2201], start_period, end_period).values[0, 0])


def pso_portfolio(asset_ids):
    """
    Optimize the number of each asserts in the portfolio

    The asserts themselves cannot be changed

    Parameters
    ----------  
    assets : array
        Assets id in the portfolio
    """

    portefolio_id = get_epita_portfolio_id()
    portefolio = get_epita_portfolio()
    nb_assets = len(asset_ids)

    def constraints_list(x, asset_ids, c, d):
        s = np.sum(x) - 1
        f = is_fund_or_etf_or_index(x, asset_ids) - 0.49
        lb = [rend_calc(asset_ids, x, i) - 0.1 for i in range(len(asset_ids))]
        ub = [0.01 - rend_calc(asset_ids, x, i) for i in range(len(asset_ids))]
        res = [s, f]
        res.append(lb[0])
        res.append(ub[0])
        return res

    constraints = constraints_list

    lb = [0] * nb_assets
    ub = [1] * nb_assets

    xopt, fopt = pso(minimize_negative_sharpe, lb, ub, args=(
        asset_ids, portefolio_id, portefolio))
    print(xopt)
    optimal_sharpe_arr = xopt * 100000
    print(f"[DEBUG] After optimization : {optimal_sharpe_arr}")
    print("sharp of portfolio =", post_operations(
        [12], [portefolio_id], start_period, end_period).values[0, 0])
    print("sharp of ref =", post_operations(
        [12], [2201], start_period, end_period).values[0, 0])
