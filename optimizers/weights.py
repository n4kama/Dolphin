import numpy as np
import pandas as pd
from pyswarm import pso
import scipy.optimize as optimize

from DolphinApi.config import *
from optimizers.utils import *


def get_v_r_s():
    try:
        back_val_table = pd.read_csv("back_val_table.csv", index_col=0)
    except FileNotFoundError:
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
        back_val_table = assets
        back_val_table.to_csv("back_val_table.csv")
    try:
        v_r_s = pd.read_csv("v_r_s.csv", index_col=0)
    except FileNotFoundError:
        print(back_val_table.ASSET_DATABASE_ID.values)
        v_r_s = post_operations(
            [10, 12, 13], back_val_table.ASSET_DATABASE_ID.tolist(), start_period, end_period)
        v_r_s.to_csv("v_r_s.csv")

    return v_r_s


def process_val_back(id_, w):
    try:
        back_val_table = pd.read_csv("back_val_table.csv", index_col=0)
    except FileNotFoundError:
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
        back_val_table = assets
        back_val_table.to_csv("back_val_table.csv")

    asset_min_buy = back_val_table[back_val_table['ASSET_DATABASE_ID']
                                   == id_].MIN_BUY_AMOUNT.values[0]
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

    # assets_dataframe['weighths']

    # Put portfolio
    put_portfolio(portefolio_id, portefolio, assets_dataframe)

    # must do at least once..
    post_operations([12], [portefolio_id], start_period, end_period)
    sharp = post_operations([12], [portefolio_id],
                            start_period, end_period).values[0, 0]

    # print(sharp)
    return -sharp


def min_func(weights, asset_ids, portefolio_id, portefolio):
    """
    Minimize the negative sharpe on the entire portfolio

    Since optimize.minimize seeks to minimize, we return
    the negative of our portfolio sharpe (which we want to be big)
    """

    # arrange weights given min_buy
    weights = np.array([process_val_back(asset_ids[i], weights[i]*100000)
                        for i in range(len(asset_ids))])

    # Update portfolio with new weights
    assets_dataframe = pd.DataFrame(
        data={'asset_id': asset_ids, 'quantities': weights})

    vrs_df = get_v_r_s()
    returns = vrs_df.loc[asset_ids, :].Rendement.values
    volas = np.sqrt(np.dot(weights.T, np.dot(
        np.cov(np.log(returns)), weights)))
    sharpes = vrs_df.Sharpe.values
    sharpe = ((np.dot(returns, weights) - 0.05) / volas)
    print(sharpe)

    # print(sharp)
    return sharpe


def is_fund_or_etf_or_index(x, asset_ids):
    res = 0
    for i, id_ in enumerate(asset_ids):
        res = x[i] if get_type(id_) != "stock" else 0
    return res


def rend_calc(asset_ids, x, i):
    rend_line = post_operations(
        [13], asset_ids, start_period, end_period).values[:, 0]
    return (rend_line[i] * x[i]) / (np.dot(np.array(rend_line), np.array(x)))


def rend_calc_(asset_ids, x, i):
    vrs_df = get_v_r_s()
    rend_line = vrs_df.loc[asset_ids, :].Rendement.values
    return (rend_line[i] * x[i]) / (np.dot(np.array(rend_line), np.array(x)))


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

    constraints = [lambda x, assets_ids, c, d: np.sum(x) - 1]
    lb = [lambda x, assets_ids, c, d: rend_calc(
        asset_ids, x, i) - 0.1 for i in range(len(asset_ids))]
    ub = [lambda x, assets_ids, c, d: 0.01 -
          rend_calc(asset_ids, x, i) for i in range(len(asset_ids))]
    constraints.append(lb[0])
    constraints.append(ub[0])

    lb = [0] * nb_assets
    ub = [1] * nb_assets

    xopt, fopt = pso(minimize_negative_sharpe, lb, ub, ieqcons=constraints, args=(
        asset_ids, portefolio_id, portefolio), debug=True)
    print(xopt)
    optimal_sharpe_arr = xopt * 100000
    print(f"[DEBUG] After optimization : {optimal_sharpe_arr}")
    print("sharp of portfolio =", post_operations(
        [12], [portefolio_id], start_period, end_period).values[0, 0])
    print("sharp of ref =", post_operations(
        [12], [2201], start_period, end_period).values[0, 0])
    return np.array(optimal_sharpe_arr)


def opti_pso_portfolio(asset_ids):
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

    constraints = [lambda x, assets_ids, c, d: np.sum(x) - 1]
    lb = [lambda x, assets_ids, c, d: rend_calc(
        asset_ids, x, i) - 0.1 for i in range(len(asset_ids))]
    ub = [lambda x, assets_ids, c, d: 0.01 -
          rend_calc(asset_ids, x, i) for i in range(len(asset_ids))]
    constraints.append(lb[0])
    constraints.append(ub[0])

    lb = [0] * nb_assets
    ub = [1] * nb_assets

    xopt, fopt = pso(min_func, lb, ub, ieqcons=constraints, args=(
        asset_ids, portefolio_id, portefolio), debug=True)
    print(xopt)
    optimal_sharpe_arr = xopt * 100000
    print(f"[DEBUG] After optimization : {optimal_sharpe_arr}")
    print("sharp of portfolio =", post_operations(
        [12], [portefolio_id], start_period, end_period).values[0, 0])
    print("sharp of ref =", post_operations(
        [12], [2201], start_period, end_period).values[0, 0])
    return np.array(optimal_sharpe_arr)


def wrap_optimise(assets_ids, fast):
    data = get_quote_matrixes(start_period, end_period)[
        1].fillna(method='bfill')
    stock_counter = 1
    return_matrix = []
    cov_input = []

    for i in assets_ids:
        avg_return = data[str(i)].values.mean()
        return_matrix.append(avg_return)
        cov_input.append(data[str(i)].tolist())

    return_matrix = np.matrix(return_matrix)
    cov_input = np.matrix(cov_input)
    cov_matrix = np.cov(cov_input)

    return opti_portfolio(assets_ids, return_matrix, cov_matrix, fast)


def opti_portfolio(asset_ids, return_matrix, cov_matrix, fast):
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

    lb = [0] * nb_assets
    lb2 = [0.01] * nb_assets
    ub = [0.1] * nb_assets

    constraints = [lambda x, assets_ids, c, d: np.sum(x) - 1]

    if(not fast):
        xopt, fopt = pso(opti_min_func, lb2, ub, ieqcons=constraints, args=(
            asset_ids, return_matrix, cov_matrix), swarmsize=1000, maxiter=30)
    else:
        xopt, fopt = pso(opti_min_func, lb, ub, ieqcons=constraints, args=(
            asset_ids, return_matrix, cov_matrix), debug=False, swarmsize=100, maxiter=30, minstep=1e-4)

    print(xopt)
    optimal_sharpe_arr = xopt
    return np.array(optimal_sharpe_arr)


def opti_min_func(weights, assets_id, return_matrix, cov_matrix):
    """
    Function to calculate Sharpe ratio
    """
    weights = [w / sum(weights) for w in weights]
    weights = np.matrix(weights)
    port_return = np.round(np.sum(weights * return_matrix.T) * 1274, 2)/5
    port_volacity = np.round(
        np.sqrt(weights * cov_matrix * weights.T) * np.sqrt(1274), 2)/np.sqrt(5)
    sharpe_ratio = (port_return - 0.05) / float(port_volacity)
    return - sharpe_ratio


def stock_constraint(x, assets_ids):
    complete_price = 0
    stocks_price = 0
    for i, id_ in enumerate(assets_ids):
        cur_price = get_price(id_) * x[i]
        if(get_type(id_) == "STOCK"):
            stocks_price += cur_price
        complete_price += cur_price
    return stocks_price / complete_price


def together_opti(assets_ids, fast):
    data = get_quote_matrixes(start_period, end_period)[
        1].fillna(method='bfill')
    stock_counter = 1
    return_matrix = []
    cov_input = []

    for i in assets_ids:
        avg_return = data[str(i)].values.mean()
        return_matrix.append(avg_return)
        cov_input.append(data[str(i)].tolist())

    return_matrix = np.matrix(return_matrix)
    cov_input = np.matrix(cov_input)
    cov_matrix = np.cov(cov_input)

    portefolio_id = get_epita_portfolio_id()
    portefolio = get_epita_portfolio()
    nb_assets = len(assets_ids)

    lb = [0] * nb_assets
    lb2 = [0.01] * nb_assets
    ub = [0.1] * nb_assets

    constraints = [lambda x, assets_ids, c, d: np.sum(x) - 1,
                   lambda x, assets_ids, c, d: stock_constraint(x, assets_ids) - 0.51]

    if(not fast):
        xopt, fopt = pso(opti_min_func, lb2, ub, ieqcons=constraints, args=(
            assets_ids, return_matrix, cov_matrix), debug=True, swarmsize=1000, maxiter=30)
    else:
        xopt, fopt = pso(opti_min_func, lb, ub, ieqcons=[constraints[0]], args=(
            assets_ids, return_matrix, cov_matrix), debug=False, swarmsize=100, maxiter=30, minstep=1e-4)

    print(xopt)
    optimal_sharpe_arr = xopt
    return np.array(optimal_sharpe_arr)
