import numpy as np
import pandas as pd

from pyswarm import pso
import scipy.optimize as optimize

from DolphinApi.config import *
from optimizers.tables import *
from optimizers.portfolio import *


def opti_min_func(weights, assets_id, return_matrix, cov_matrix, prices):
    """
    Function to calculate Sharpe ratio
    """
    true_w = np.round((weights * 100000000) / prices)
    weights = [w / sum(true_w) for w in true_w]
    weights = np.matrix(weights)
    port_return = np.round(np.sum(weights * return_matrix.T) * 1274, 2)/5
    port_volacity = np.round(
        np.sqrt(weights * cov_matrix * weights.T) * np.sqrt(1274), 2)/np.sqrt(5)
    sharpe_ratio = (port_return - 0.05) / float(port_volacity)
    return - sharpe_ratio


def pso_optimise(assets_ids, fast):
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

    fast_lb = [0] * nb_assets
    lb, ub = [0.015] * nb_assets, [0.095] * nb_assets

    constraints = [lambda x, assets_ids, c, d, e: np.sum(x) - 1]

    prices = get_prices(assets_ids)

    if(fast):
        xopt, fopt = pso(opti_min_func, fast_lb, ub, ieqcons=[constraints[0]], args=(
            assets_ids, return_matrix, cov_matrix, prices), debug=True, swarmsize=200, maxiter=10, minstep=1e-3)
    else:
        xopt, fopt = pso(opti_min_func, lb, ub, ieqcons=constraints, args=(
            assets_ids, return_matrix, cov_matrix, prices), debug=True, swarmsize=1500, maxiter=30)

    return np.array(xopt)


def scipy_optimise(assets_ids, fast):
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

    # ws = np.random.dirichlet(np.ones(10),size=1)
    ws = [1/nb_assets] * nb_assets

    fast_rangeb = tuple((0, 0.1) for i in range(nb_assets))
    rangeb = tuple((0.012, 0.098) for i in range(nb_assets))


    prices = get_prices(assets_ids)

    if(fast):
        xopt = optimize.minimize(opti_min_func,
                                 ws,
                                 (assets_ids, return_matrix, cov_matrix, prices),
                                 method='TNC',
                                 options={'maxiter': 2500, 'ftol': 1e-09, 'disp': True, 'eps': 0.001},
                                 bounds=fast_rangeb)
    else:
        xopt = optimize.minimize(opti_min_func,
                                 ws,
                                 (assets_ids, return_matrix, cov_matrix, prices),
                                 method='TNC',
                                 options={'maxiter': 5000, 'ftol': 1e-08, 'disp': True, 'eps': 0.000001},
                                 bounds=fast_rangeb)


    return np.array(xopt.x)
