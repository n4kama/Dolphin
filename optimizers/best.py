from DolphinApi.config import *
from optimizers.weights import pso_optimise, scipy_optimise, stock_constraint, nav_constraint

from optimizers.portfolio import *
from optimizers.utils import *
from optimizers.tables import *

import numpy as np
import pandas as pd


def post_operations(ratios, ids, start, end, bench=None, frequency=None):
    """
    Post request to the API

    Parameters
    ----------
    ratios  : array
        array of the operations to compute
    ids     : array
        array the assets IDs
    start   : date
        format: 'Y-m-d'
    end     : date
        format: 'Y-m-d'
    Returns
    -------
        Dataframe of the response
    """

    payload = {'ratio': ratios,
               'asset': ids,
               'start_date': start,
               'end_date': end,
               'bench': bench,
               'frequency': frequency}
    data = api.post('ratio/invoke', payload)
    data = pd.read_json(data)
    operation = convert_type(data)
    operation = operation.transpose()
    operation.columns = np.array(
        [api.operations_table[api.operations_table.id == i].name.values[0] for i in ratios])
    return operation


def check_constraints(assets_ids, x):
    prices = get_prices(assets_ids)
    stocks = get_types_ids(assets_ids, ["STOCK"])
    print("stock part %:", stock_constraint_b(x, prices, np.array(stocks).astype(int))*100)
    print("%nav between 0.01 and 0.1:", stock_constraint_b(x, prices, np.array(stocks).astype(int)))
    print("assets between 15 and 40:", len(assets_ids) > 14 and len(assets_ids) < 41)


def sharping_together(algo_opti):
    stock_ids = select_type(["STOCK"])
    fund_ids = select_type(["ETF FUND", "FUND", "INDEX"])
    portefolio_id = get_epita_portfolio_id()
    portefolio = get_epita_portfolio()

    print("STOCKS")
    stock_part = algo_opti(stock_ids, True)
    df = pd.DataFrame(np.stack((stock_ids, stock_part), axis=-1),
                      columns=["ids", "part"]).sort_values(by="part").values
    stock_ids = df[:, 0][::-1][:40].astype(int)

    print("NOT STOCKS")
    fund_part = algo_opti(fund_ids, True)
    df = pd.DataFrame(np.stack((fund_ids, fund_part), axis=-1),
                      columns=["ids", "part"]).sort_values(by="part").values
    fund_ids = df[:, 0][::-1][:0].astype(int)  # replace 100 by 5 at worst case

    print("REDUCE PART")
    reduced_ids = np.concatenate((stock_ids, fund_ids))
    reduced_part = algo_opti(reduced_ids, True)
    df = pd.DataFrame(np.stack((reduced_ids, reduced_part), axis=-1),
                      columns=["ids", "part"]).sort_values(by="part").values
    final_ids = df[:, 0][::-1][:15].astype(int)

    print("COMPUTE BEST")
    final_part = algo_opti(final_ids, False)

    check_constraints(final_ids, final_part)

    assets_dataframe = pd.DataFrame(
        data={'asset_id': final_ids, 'quantities': final_part * 1000000})

    print(assets_dataframe)
    put_portfolio(portefolio_id, portefolio, assets_dataframe)
    post_operations([12], [portefolio_id], start_period,
                    end_period).values[0, 0]
    print("sharp of portfolio =", post_operations(
        [12], [portefolio_id], start_period, end_period).values[0, 0])

    return final_part


def sharping_stocks(algo_opti):
    stock_ids = select_type(["STOCK"])
    portefolio_id = get_epita_portfolio_id()
    portefolio = get_epita_portfolio()

    print("REDUCE")
    stock_part = algo_opti(stock_ids, True)
    df = pd.DataFrame(np.stack((stock_ids, stock_part), axis=-1),
                      columns=["ids", "part"]).sort_values(by="part").values
    final_ids = df[:, 0][::-1][:40].astype(int)


    print("COMPUTE BEST")
    final_part = algo_opti(final_ids, False)

    check_constraints(final_ids, final_part)

    assets_dataframe = pd.DataFrame(
        data={'asset_id': final_ids, 'quantities': final_part * 1000000})

    print(assets_dataframe)
    put_portfolio(portefolio_id, portefolio, assets_dataframe)
    post_operations([12], [portefolio_id], start_period,
                    end_period).values[0, 0]
    print("sharp of portfolio =", post_operations(
        [12], [portefolio_id], start_period, end_period).values[0, 0])

    return final_part


def get_best_weigth(algo):
    if(algo == "scipy"):
        return sharping_stocks(scipy_optimise)
    elif (algo == "pso"):
        return sharping_stocks(pso_optimise)
    else:
        print("choose an algorithm : 'pso' or 'scipy'")
