import numpy as np
import pandas as pd
import scipy.optimize as optimize

from dolphinApi.config import *
from optimizers.utils import *
from optimizers.reduce import choose_from


def minimize_negative_sharpe(weights, asset_ids, portefolio_id, portefolio):
    """
    Minimize the negative sharpe on the entire portfolio

    Since optimize.minimize seeks to minimize, we return
    the negative of our portfolio sharpe (which we want to be big)
    """

    # Update portfolio with new weights
    assets_dataframe = pd.DataFrame(data={'asset_id': asset_ids, 'quantities': weights})
    print(weights)
    # Put portfolio
    put_portfolio(portefolio_id, portefolio, assets_dataframe)
    # Get and return computed sharpe value

    sharp = post_operations([12], [portefolio_id], start_period, end_period).iloc[0,0]
    # return -sum([weights[i] * asset_ids[i] for i in range(len(asset_ids))])
    
    print(sharp)
    return -sharp

def optimize_portfolio(asset_ids):
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

    weights = [1] * nb_assets
    weights[-1] = 1001 - sum(weights)

    weights = (np.random.dirichlet(np.ones(nb_assets-1),size=1)*100)[0]
    weights = list(weights)
    weights.append(100 - sum(weights))

    print(weights)
    print(asset_ids)
    
    constraints = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 100},)
                #    {'type': 'eq', 'fun': lambda x: max([x[i]-int(x[i]) for i in range(len(x))])})

    bounds = tuple((1, 10) for x in range(nb_assets))
    # entre 0 et le volume de l'asset à la date de départ
    # chaque valeur doit etre [1,10]% du %nav

    optimal_sharpe = optimize.minimize(minimize_negative_sharpe,
                                       weights,
                                       (asset_ids, portefolio_id, portefolio),
                                       method='SLSQP',
                                       options={'maxiter': 100, 'ftol': 1e-06, 'iprint': 1, 'disp': False, 'eps': 0.3, 'finite_diff_rel_step': None},
                                       bounds=bounds,
                                       constraints=constraints)
    optimal_sharpe_arr = optimal_sharpe['x']
    print(f"[DEBUG] After optimization : {optimal_sharpe_arr}")
    print("sharp of portfolio =", post_operations([12], [portefolio_id], start_period, end_period).iloc[0,0])
    print("sharp of ref =", post_operations(
        [12], [2201], start_period, end_period).iloc[0,0])


def best_sharper():
    arr = choose_from(start_period, end_period, 40)
    optimize_portfolio(arr)
