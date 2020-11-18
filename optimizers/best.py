from DolphinApi.config import *
from optimizers.reduce import choose_from, select_type
from optimizers.weights import neo_opti_portfolio, pso_portfolio, opti_pso_portfolio, wrap_optimise
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


def to_step_best_sharper():
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
    removable_ids = stock_part < 0.01
    stock_part[removable_ids] = 0
    stock_part = wrap_optimise(stock_ids, False)

    print("NOT STOCKS")
    fund_part = wrap_optimise(fund_ids, True)
    df = pd.DataFrame(np.stack((fund_ids, fund_part), axis=-1),
                      columns=["ids", "part"]).sort_values(by="part").values
    fund_part = df[:, 1][::-1][:15]
    fund_ids = df[:, 0][::-1][:15].astype(int)
    removable_ids = fund_part < 0.01
    fund_part[removable_ids] = 0
    fund_part = wrap_optimise(fund_ids, False)

    print("GATHER ALL")
    stock_part = stock_part * 0.51
    fund_part = fund_part * 0.49

    final_part = np.concatenate((stock_part, fund_part))
    asset_ids = np.concatenate((stock_ids, fund_ids))

    assets_dataframe = pd.DataFrame(
        data={'asset_id': asset_ids, 'quantities': final_part * 1000000})

    print(assets_dataframe)
    put_portfolio(portefolio_id, portefolio, assets_dataframe)
    post_operations([12], [portefolio_id], start_period,
                    end_period).values[0, 0]
    print("sharp of portfolio =", post_operations(
        [12], [portefolio_id], start_period, end_period).values[0, 0])
