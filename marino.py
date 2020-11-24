from optimizers.best import get_best_weigth, rate_portfolio
import sys

algo = sys.argv[1]
try:
    both = sys.argv[2]
except:
    both = False
try:
    multi = sys.argv[3]
except:
    multi = False


try:
    res = get_best_weigth(algo=algo, both=both, multi=multi)
    rate_portfolio(res)
except:
    print("An error occured")
