# Import libraries
import pandas as pd
import collections
import datetime as dt
from scipy import stats
from alpaca import Alpaca
# AR example
from statsmodels.tsa.ar_model import AutoReg
# import warnings filter
from warnings import simplefilter
# ignore all future warnings
simplefilter(action='ignore', category=FutureWarning)


def prediction_model(histdata,days):
    slopedata = []
    output = []

    for ticker in histdata:
        for d in histdata[ticker]:
            data = {'Ticker': ticker, 'Date': d.t, 'Price': d.c}
            #print(data)
            slopedata.append(data)

    #Convert panda data to list for analysis. Data is going to be grouped by ticker and iterated. 
    grouped = collections.defaultdict(list)
    for item in slopedata:
        grouped[item['Ticker']].append(item)

    for s in grouped:
        slopelist = []
        for i in grouped[s]:
            data = [i['Date'],i['Price']]
            #print(data)
            slopelist.append(data)
            
        #logic to caluclate Slope HERE
        #print(slopelist)

        df = pd.DataFrame(slopelist, columns=['date', 'value'])
        df.date = pd.to_datetime(df.date)
        df['date_ordinal'] = pd.to_datetime(df['date']).map(dt.datetime.toordinal)
        slope, intercept, r_value, p_value, std_err = stats.linregress(df['date_ordinal'], df['value'])
        #print(stats.linregress(df['date_ordinal'], df['value']))

        if len(df['value']) == days:
            #Do prediction based on AutoReg Model
            # contrived dataset
            data = df['value']
            # fit model
            model = AutoReg(data, lags=1)
            model_fit = model.fit()
            # make prediction
            yhat = model_fit.predict(len(data), len(data))


            #Slope Trend
            #print(s, round(slope, 2))
            if slope > 0:
                trend = "UP"
            else:
                trend = "DOWN"

            ## To get coefficient of determination (r_squared) The Higher the % the more numbers fall within the line 
            #print(s, "Acuracy:", round(r_value**2*100,2),"%")
            #print(s, "Next Price:", yhat[days])
            output.append({"Stock": s, "Acuracy": round(r_value**2*100,2), "Next Price": round(yhat[days],2), "Slope": round(slope, 2), "Trend": trend})
    return(output)
