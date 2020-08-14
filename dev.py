import alpaca_trade_api as tradeapi
import json
import statistics
import numpy as np



with open('config.json') as json_file:
    config = json.load(json_file)

    key = config['Account']['API-Key']
    secret = config['Account']['Secret']
    url = config['Account']['URL']

    api = tradeapi.REST(key, secret, base_url=url) # or use ENV Vars shown below
        

out = api.get_barset('AMD','day',12)

ar = []

for o in out['AMD']:
   ar.append(o.v)

print(ar)



an_array = np.array(ar)
mean = np.mean(an_array)
standard_deviation = np.std(an_array)
distance_from_mean = abs(an_array - mean)
max_deviations = 1.5
not_outlier = distance_from_mean < max_deviations * standard_deviation
no_outliers = an_array[not_outlier]
print(no_outliers)