from DolphinApi.config import *
from optimizers.reduce import choose_from
from optimizers.weights import neo_opti_portfolio, pso_portfolio, opti_pso_portfolio
from optimizers.utils import *

import numpy as np
import pandas as pd

def best_sharper(type, nb):
    stock_ids = choose_from(start_period, end_period, nb // 2, True)
    fund_ids = choose_from(start_period, end_period, nb // 2, False)
    portefolio_id = get_epita_portfolio_id()
    portefolio = get_epita_portfolio()

    print("STOCKS")
    if(type == "pso"):
        stock_part = pso_portfolio(stock_ids)
    if(type == "opti"):
        stock_part = opti_pso_portfolio(stock_ids)
    elif(type == "neo"):
        stock_part = neo_opti_portfolio(stock_ids)
    else:
        stock_part = pso_portfolio(stock_ids)
    
    print("NOT STOCKS")
    if(type == "pso"):
        fund_part = pso_portfolio(fund_ids)
    if(type == "opti"):
        fund_part = opti_pso_portfolio(fund_ids)
    elif(type == "neo"):
        fund_part = neo_opti_portfolio(fund_ids)
    else:
        fund_part = pso_portfolio(fund_ids)

    print("GATHER ALL")
    stock_part = stock_part * 0.51
    fund_part = fund_part * 0.49
    final_part = np.concatenate((stock_part, fund_part))
    asset_ids = np.concatenate((stock_ids, fund_ids))
    assets_dataframe = pd.DataFrame(data={'asset_id': asset_ids, 'quantities': final_part})
    print(assets_dataframe)
    put_portfolio(portefolio_id, portefolio, assets_dataframe)
    post_operations([12], [portefolio_id], start_period, end_period).values[0, 0]
    print("sharp of portfolio =", post_operations([12], [portefolio_id], start_period, end_period).values[0, 0])
