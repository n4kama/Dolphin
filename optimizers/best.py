from DolphinApi.config import *
from optimizers.weights import pso_optimise, scipy_optimise

from optimizers.portfolio import *
from optimizers.utils import *
from optimizers.tables import *

import numpy as np
import pandas as pd
from colorama import Fore, Back, Style


def stock_constraint(x, price_mat, stock_ids):
    complete_price = np.dot(x, price_mat)
    stocks_price = np.dot(x[stock_ids], price_mat[stock_ids])
    return stocks_price / complete_price


def nav_constraint(x, price_mat, stock_ids):
    complete_price = np.dot(x, price_mat)
    stocks_price = x[stock_ids] * price_mat[stock_ids]
    nav_percent = stocks_price / complete_price
    return np.all(nav_percent) < 0.1 and np.all(nav_percent) > 0.01


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
    stocks = get_types_ids(assets_ids, ["STOCK"])
    # print("assets ids tested: ", assets_ids)
    # print("stocks are numbers: ", stocks)
    # print("stock part %:", np.sum(x[stocks]) * 100 / np.sum(x))
    # print("%nav between 0.01 and 0.1:", np.all(x <= 0.1) and np.all(x >= 0.01))
    # print("assets between 15 and 40:", len(
    #     assets_ids) > 14 and len(assets_ids) < 41)
    return len(assets_ids) > 14 and len(assets_ids) < 41 and np.all(x <= 0.1) and np.all(x >= 0.01) and (np.sum(x[stocks]) * 100 / np.sum(x)) > 50


def check_constraints_portfolio(portfolio_df):
    assets_ids = np.array(portfolio_df.asset_id.tolist())
    stocks_ids = get_types_ids(assets_ids, ["STOCK"])
    quantities = np.array(portfolio_df.quantities.tolist())
    prices = get_prices(assets_ids)
    types = get_types(assets_ids)
    total_price = np.dot(prices, quantities)
    each_price = prices * quantities

    nav = each_price / total_price
    stock_percent = np.sum(each_price[stocks_ids]) * 100 / np.sum(each_price)

    stock_percent_check = stock_percent > 50
    nav_check = np.logical_and(nav > 0.01, nav < 0.1)
    len_check = len(assets_ids) >= 15 and len(assets_ids) <= 40

    portfolio_df["close"] = prices
    portfolio_df["montant"] = each_price
    portfolio_df["nav"] = nav
    portfolio_df["types"] = types
    print(portfolio_df)

    print("---------------------")
    print("Portfolio total price:", total_price)
    print("Portfolio stock price:", np.sum(each_price[stocks_ids]))
    print("---------------------\n")
    if stock_percent_check:
        print(Fore.GREEN)
    else:
        print(Fore.RED)
    print("Stock percent        :",  stock_percent)
    if np.all(nav_check):
        print(Fore.GREEN)
    else:
        print(Fore.RED)
    print("%Nav check           :", nav_check)
    if len_check:
        print(Fore.GREEN)
    else:
        print(Fore.RED)
    print("[15;40] assets check :",  len(assets_ids))
    print(Style.RESET_ALL)

    return stock_percent_check and np.all(nav_check) and len_check


def sharping_together(algo_opti, stock_percent, fund_percent):
    portefolio_id = get_epita_portfolio_id()
    portefolio = get_epita_portfolio()

    stock_ids = select_type(["STOCK"]).tolist()
    sharps = post_operations([12], stock_ids, start_period, end_period)
    sharps = post_operations([12], stock_ids, start_period, end_period)
    stock_ids = sharps.sort_values(
        by="Sharpe", ascending=False).index[:30].tolist()

    print("REDUCE STOCKS")
    stock_part = algo_opti(stock_ids, True)

    df = pd.DataFrame(np.stack((stock_ids, stock_part), axis=-1),
                      columns=["ids", "part"]).sort_values(by="part", ascending=False).values
    sfinal_ids = df[:, 0][:16].astype(int)

    print("COMPUTE BEST STOCKS")
    sfinal_part = algo_opti(sfinal_ids, False)
    print("basic check:", check_constraints(sfinal_ids, sfinal_part))

    fund_ids = select_type(["FUND"]).tolist()
    sharps = post_operations([12], fund_ids, start_period, end_period)
    sharps = post_operations([12], fund_ids, start_period, end_period)
    fund_ids = sharps.sort_values(
        by="Sharpe", ascending=False).index[:50].tolist()

    print("REDUCE FUNDS")
    fund_part = algo_opti(fund_ids, True)
    df = pd.DataFrame(np.stack((fund_ids, fund_part), axis=-1),
                      columns=["ids", "part"]).sort_values(by="part", ascending=False).values
    ffinal_ids = df[:, 0][:16].astype(int)

    print("COMPUTE BEST FUNDS")
    ffinal_part = algo_opti(ffinal_ids, False)
    print("basic check:", check_constraints(ffinal_ids, ffinal_part))

    print("REDUCE BEST")
    final_ids = np.concatenate((sfinal_ids, ffinal_ids))
    final_part = np.concatenate(
        (sfinal_part * stock_percent, ffinal_part * fund_percent))

    prices = np.array(get_prices(final_ids))

    print("basic check:", check_constraints(final_ids, final_part))

    assets_dataframe = pd.DataFrame(
        data={'asset_id': final_ids, 'quantities': np.round((final_part * 1000000000) / prices)})

    put_portfolio(portefolio_id, portefolio, assets_dataframe)
    return assets_dataframe


def sharping_stocks(algo_opti):
    stock_ids = select_type(["STOCK"]).tolist()
    sharps = post_operations([12], stock_ids, start_period, end_period)
    sharps = post_operations([12], stock_ids, start_period, end_period)
    stock_ids = sharps.sort_values(
        by="Sharpe", ascending=False).index[:30].tolist()
    portefolio_id = get_epita_portfolio_id()
    portefolio = get_epita_portfolio()

    print("REDUCE")
    stock_part = algo_opti(stock_ids, True)
    df = pd.DataFrame(np.stack((stock_ids, stock_part), axis=-1),
                      columns=["ids", "part"]).sort_values(by="part", ascending=False).values
    final_ids = df[:, 0][:18].astype(int)

    print("COMPUTE BEST")
    final_part = algo_opti(final_ids, False)
    prices = np.array(get_prices(final_ids))

    print("basic check:", check_constraints(final_ids, final_part))

    assets_dataframe = pd.DataFrame(
        data={'asset_id': final_ids, 'quantities': np.round((final_part * 1000000000) / prices)})

    put_portfolio(portefolio_id, portefolio, assets_dataframe)
    return assets_dataframe


def get_best_weigth(algo, both, stock=0.6, fund=0.4):
    if(both):
        if(algo == "scipy"):
            return sharping_together(scipy_optimise, stock, fund)
        elif (algo == "pso"):
            return sharping_together(pso_optimise, stock, fund)
    else:
        if(algo == "scipy"):
            return sharping_stocks(scipy_optimise)
        elif (algo == "pso"):
            return sharping_stocks(pso_optimise)
    print("choose an algorithm : 'pso' or 'scipy'")


def rate_portfolio(df):
    portefolio = get_epita_portfolio()
    pid = get_epita_portfolio_id()
    put_portfolio(pid, portefolio, df)
    sp = start_period
    ep = end_period
    post_operations([12], [pid], sp, ep).values[0, 0]
    sharpe = post_operations([12], [pid], sp, ep).values[0, 0]

    print("//////////////////////////////////////")
    print(Fore.BLUE)
    print("Sharp of portfolio =", sharpe)
    print(Style.RESET_ALL)
    check_bool = check_constraints_portfolio(df)
    if check_bool:
        print(Fore.GREEN)
        print("Constraint pass: True")
    else:
        print(Fore.RED)
        print("Constraint pass: False")
    print(Style.RESET_ALL)
    print("//////////////////////////////////////")
    return sharpe, check_bool
