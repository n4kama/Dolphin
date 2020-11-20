from DolphinApi.config import *
from optimizers.reduce import choose_from, select_type
from optimizers.weights import neo_opti_portfolio, pso_portfolio, opti_pso_portfolio, wrap_optimise, together_opti
from optimizers.utils import *

import numpy as np
import pandas as pd


def best_sharper(type, nb):
    stock_ids = choose_from(start_period, end_period, nb, True)
    # fund_ids = choose_from(start_period, end_period, 0, False)
    portefolio_id = get_epita_portfolio_id()
    portefolio = get_epita_portfolio()

    print("STOCKS")
    if(type == "pso"):
        stock_part = pso_portfolio(stock_ids)
    if(type == "opti"):
        stock_part = opti_pso_portfolio(stock_ids)
    if(type == "wrap"):
        stock_part = wrap_optimise(stock_ids)
    elif(type == "neo"):
        stock_part = neo_opti_portfolio(stock_ids)
    else:
        stock_part = pso_portfolio(stock_ids)

    # print("NOT STOCKS")
    # if(type == "pso"):
    #     fund_part = pso_portfolio(fund_ids)
    # if(type == "opti"):
    #     fund_part = opti_pso_portfolio(fund_ids)
    # if(type == "wrap"):
    #     fund_part = wrap_optimise(fund_ids)
    # elif(type == "neo"):
    #     fund_part = neo_opti_portfolio(fund_ids)
    # else:
    #     fund_part = pso_portfolio(fund_ids)

    print("GATHER ALL")
    stock_part = stock_part * 0.51
    # fund_part = fund_part * 0.49
    # final_part = np.concatenate((stock_part, fund_part))
    # asset_ids = np.concatenate((stock_ids, fund_ids))
    final_part = stock_part
    asset_ids = stock_ids

    df = pd.DataFrame(np.stack((asset_ids, final_part), axis=-1),
                      columns=["ids", "part"]).sort_values(by="part").values
    final_part = df[:, 1][::-1][:40]
    asset_ids = df[:, 0][::-1][:40].astype(int)
    removable_ids = final_part < 0.01
    final_part[removable_ids] = 0

    print("REOPTIMISE")
    if(type == "pso"):
        final_part = pso_portfolio(asset_ids)
    if(type == "opti"):
        final_part = opti_pso_portfolio(asset_ids)
    if(type == "wrap"):
        final_part = wrap_optimise(asset_ids)
    elif(type == "neo"):
        final_part = neo_opti_portfolio(asset_ids)
    else:
        final_part = pso_portfolio(asset_ids)

    removable_ids = final_part < 0.01
    final_part[removable_ids] = 0
    # ne pas oublier de recalculer les poids en fonction du min_buy
    assets_dataframe = pd.DataFrame(
        data={'asset_id': asset_ids, 'quantities': final_part * 100000})
    print(assets_dataframe)
    put_portfolio(portefolio_id, portefolio, assets_dataframe)
    post_operations([12], [portefolio_id], start_period,
                    end_period).values[0, 0]
    print("sharp of portfolio =", post_operations(
        [12], [portefolio_id], start_period, end_period).values[0, 0])


def two_step_best_sharper():
    stock_ids = select_type(["STOCK"])
    fund_ids = select_type(["ETF FUND", "FUND", "INDEX"])
    portefolio_id = get_epita_portfolio_id()
    portefolio = get_epita_portfolio()

    print("STOCKS")
    stock_part = wrap_optimise(stock_ids, True)
    df = pd.DataFrame(np.stack((stock_ids, stock_part), axis=-1),
                      columns=["ids", "part"]).sort_values(by="part").values
    stock_part = df[:, 1][::-1][:15]
    stock_ids = df[:, 0][::-1][:15].astype(int)
    stock_part = wrap_optimise(stock_ids, False)

    print("NOT STOCKS")
    fund_part = wrap_optimise(fund_ids, True)
    df = pd.DataFrame(np.stack((fund_ids, fund_part), axis=-1),
                      columns=["ids", "part"]).sort_values(by="part").values
    fund_part = df[:, 1][::-1][:15]
    fund_ids = df[:, 0][::-1][:15].astype(int)
    fund_part = wrap_optimise(fund_ids, False)

    print("GATHER ALL")
    stock_part = stock_part * 0.51
    fund_part = fund_part * 0.49

    final_part = np.concatenate((stock_part, fund_part))
    asset_ids = np.concatenate((stock_ids, fund_ids))

    print(final_part)
    assets_dataframe = pd.DataFrame(
        data={'asset_id': asset_ids, 'quantities': final_part * 1000000})

    print(assets_dataframe)
    put_portfolio(portefolio_id, portefolio, assets_dataframe)
    post_operations([12], [portefolio_id], start_period,
                    end_period).values[0, 0]
    print("sharp of portfolio =", post_operations(
        [12], [portefolio_id], start_period, end_period).values[0, 0])

    return final_part

def stock_constraint(x, assets_ids):
    complete_price = 0
    stocks_price = 0
    for i, id_ in enumerate(assets_ids):
        cur_price = get_price(id_) * x[i]
        if(get_type(id_) == "STOCK"):
            stocks_price += cur_price
        complete_price += cur_price
    return stocks_price / complete_price

def check_constraints(assets_ids, x):
    print("stock part superior to 50%:", stock_constraint(x, assets_ids) > 0.5)
    print("%nav between 0.01 and 0.1:", np.all(x < 0.1) and np.all(x > 0.01))
    print("assets between 15 and 40:", len(assets_ids) > 14 and len(assets_ids) < 41)


def sharping_together():
    stock_ids = select_type(["STOCK"])
    fund_ids = select_type(["ETF FUND", "FUND", "INDEX"])
    portefolio_id = get_epita_portfolio_id()
    portefolio = get_epita_portfolio()

    print("STOCKS")
    stock_part = together_opti(stock_ids, True)
    df = pd.DataFrame(np.stack((stock_ids, stock_part), axis=-1),
                      columns=["ids", "part"]).sort_values(by="part").values
    stock_ids = df[:, 0][::-1][:40].astype(int)

    print("NOT STOCKS")
    fund_part = together_opti(fund_ids, True)
    df = pd.DataFrame(np.stack((fund_ids, fund_part), axis=-1),
                      columns=["ids", "part"]).sort_values(by="part").values
    fund_ids = df[:, 0][::-1][:40].astype(int)

    print("REDUCE PART")
    reduced_ids = np.concatenate((stock_ids, fund_ids))
    reduced_part = together_opti(reduced_ids, True)
    df = pd.DataFrame(np.stack((reduced_ids, reduced_part), axis=-1),
                      columns=["ids", "part"]).sort_values(by="part").values
    final_ids = df[:, 0][::-1][:40].astype(int)

    print("COMPUTE BEST")
    final_part = together_opti(final_ids, False)

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
