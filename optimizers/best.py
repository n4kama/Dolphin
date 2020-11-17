from DolphinApi.config import *
from optimizers.reduce import choose_from
from optimizers.weights import neo_opti_portfolio, pso_portfolio
from optimizers.utils import *

import numpy as np
import pandas as pd

def best_sharper(type, nb):
    arr = choose_from(start_period, end_period, nb // 2, True)
    arr2 = choose_from(start_period, end_period, nb // 2, False)
    portefolio_id = get_epita_portfolio_id()
    portefolio = get_epita_portfolio()
    print("STOCKS")
    if(type == "pso"):
        stock_part = pso_portfolio(arr)
    elif(type == "neo"):
        stock_part = neo_opti_portfolio(arr)
    else:
        stock_part = pso_portfolio(arr)
    
    print("NOT STOCKS")
    if(type == "pso"):
        fund_part = pso_portfolio(arr2)
    elif(type == "neo"):
        fund_part = neo_opti_portfolio(arr2)
    else:
        fund_part = pso_portfolio(arr2)

    print("GATHER")
    stock_part = stock_part * 0.51
    fund_part = fund_part * 0.49
    final_part = np.concatenate((stock_part, fund_part))
    asset_ids = np.concatenate((arr, arr2))
    assets_dataframe = pd.DataFrame(data={'asset_id': asset_ids, 'quantities': final_part})
    # Put portfolio
    print(assets_dataframe)
    put_portfolio(portefolio_id, portefolio, assets_dataframe)
    post_operations([12], [portefolio_id], start_period, end_period).values[0, 0]
    print("sharp of portfolio =", post_operations([12], [portefolio_id], start_period, end_period).values[0, 0])
    print(get_epita_portfolio())