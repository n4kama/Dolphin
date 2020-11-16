from DolphinApi.config import *
from optimizers.reduce import choose_from
from optimizers.weights import neo_opti_portfolio, pso_portfolio


def best_sharper(type, nb):
    arr = choose_from(start_period, end_period, nb)
    if(type == "pso"):
        pso_portfolio(arr)
    elif(type == "neo"):
        neo_opti_portfolio(arr)
    else:
        pso_portfolio(arr)
