from DolphinApi.config import *
from optimizers.reduce import choose_from
from optimizers.weights import neo_opti_portfolio, pso_portfolio


def best_sharper(type, nb):
    arr = choose_from(start_period, end_period, nb // 2, True)
    arr2 = choose_from(start_period, end_period, nb // 2, False)
    
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
    final_part = np.concatenate(0.51*stock_part, 0.49*fund_part)
    assets_dataframe = pd.DataFrame(data={'asset_id': asset_ids, 'quantities': final_part})
    # Put portfolio
    put_portfolio(portefolio_id, portefolio, assets_dataframe)
    post_operations([12], [portefolio_id], start_period, end_period).values[0, 0]
    print("sharp of portfolio =", post_operations([12], [portefolio_id], start_period, end_period).values[0, 0])