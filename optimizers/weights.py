import numpy as np
import pandas as pd

from pyswarm import pso
import scipy.optimize as optimize

from DolphinApi.config import *
from optimizers.tables import *
from optimizers.portfolio import *


def stock_constraint(x, price_mat, stock_ids):
    complete_price = np.dot(x, price_mat)
    stocks_price = np.dot(x[stock_ids], price_mat[stock_ids])
    return stocks_price / complete_price


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
    lb = [0.01] * nb_assets
    ub = [0.1] * nb_assets

    prices = get_prices(assets_ids)
    stocks = get_types_ids(assets_ids, ["STOCK"])

    constraints = [lambda x, assets_ids, c, d: np.sum(x) - 1,
                   lambda x, assets_ids, c, d: stock_constraint(x, prices, np.array(stocks).astype(int)) - 0.51]

    if(not fast):
        xopt, fopt = pso(opti_min_func, lb, ub, ieqcons=[constraints[0]], args=(
            assets_ids, return_matrix, cov_matrix), debug=True, swarmsize=1000, omega=0.9, phip=0.1, phig=0.1, maxiter=20)
    else:
        xopt, fopt = pso(opti_min_func, fast_lb, ub, ieqcons=[constraints[0]], args=(
            assets_ids, return_matrix, cov_matrix), debug=True, swarmsize=100, maxiter=20, minstep=1e-4)

    print(xopt)
    optimal_sharpe_arr = xopt
    return np.array(optimal_sharpe_arr)


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

    ws = [1/nb_assets] * nb_assets

    fast_rangeb = tuple((0, 0.1) for i in range(nb_assets))
    rangeb = tuple((0.01, 0.1) for i in range(nb_assets))

    constraints = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1},)

    if(not fast):
        xopt = optimize.minimize(opti_min_func,
                                 ws,
                                 (assets_ids, return_matrix, cov_matrix),
                                 method='SLSQP',
                                 options={'maxiter': 500, 'ftol': 1e-06,
                                          'iprint': 1, 'disp': True, 'eps': 0.1},
                                 bounds=rangeb,
                                 constraints=constraints)
    else:
        xopt = optimize.minimize(opti_min_func,
                                 ws,
                                 (assets_ids, return_matrix, cov_matrix),
                                 method='SLSQP',
                                 options={'maxiter': 500, 'ftol': 1e-07,
                                          'iprint': 1, 'disp': False, 'eps': 0.1},
                                 bounds=fast_rangeb,
                                 constraints=constraints)

    print(xopt)
    optimal_sharpe_arr = xopt.x
    return np.array(optimal_sharpe_arr)
