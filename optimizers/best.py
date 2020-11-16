from DolphinApi.config import *
from optimizers.reduce import choose_from
from optimizers.weights import optimize_portfolio, neo_opti_portfolio, pso_portfolio


def best_sharper():
    arr = choose_from(start_period, end_period, 40)
    pso_portfolio(arr)
