import alpaca_trade_api as tradeapi
import json
import statistics


class Alpaca:   
    # init method or constructor    
    def __init__(self):   
        #Read Config file
        with open('config.json') as json_file:
            config = json.load(json_file)

            key = config['Account']['API-Key']
            secret = config['Account']['Secret']
            url = config['Account']['URL']

        self.api = tradeapi.REST(key, secret, base_url=url) # or use ENV Vars shown below
        
    def account(self):   
        return(self.api.get_account())

    def lastquote(self,symbol):   
        return(self.api.get_last_quote(symbol))

    def history(self,symbol,timeframe,limit):   
        return(self.api.get_barset(symbol,timeframe,limit))

    def avgLow(self,symbols,timeframe,limit):
        #get % of flux, high/low based on timeframe and snapshot period
        #ie: show average daily fluctuation in price over 5 days. or do hourly fluctionation over 2 days. 
        histdata = self.history(symbols,timeframe,limit)
        outdata = []

        for symbol in symbols:
            changes_in_percent = []
            for d in histdata[symbol]:
                changes_in_percent.append(round(d.l,2))
            outdata.append([symbol,round(statistics.mean(changes_in_percent),2)])

        return(outdata)

    def avgHigh(self,symbols,timeframe,limit):
        #get % of flux, high/low based on timeframe and snapshot period
        #ie: show average daily fluctuation in price over 5 days. or do hourly fluctionation over 2 days. 
        histdata = self.history(symbols,timeframe,limit)
        outdata = []

        for symbol in symbols:
            changes_in_percent = []
            for d in histdata[symbol]:
                changes_in_percent.append(round(d.h,2))
            outdata.append([symbol,round(statistics.mean(changes_in_percent),2)])

        return(outdata)

    def volatility(self,symbols,timeframe,limit):
        #get % of flux, high/low based on timeframe and snapshot period
        #ie: show average daily fluctuation in price over 5 days. or do hourly fluctionation over 2 days. 
        histdata = self.history(symbols,timeframe,limit)
        outdata = []
        for symbol in symbols:
            changes_in_percent = []
            for d in histdata[symbol]:
                #print('Sym ',symbol)
                #print('Low ',d.l)
                #print('High' ,d.h)
                changes_in_percent.append(round(((d.h - d.l)/d.l) * 100,2))
            outdata.append([symbol,round(statistics.mean(changes_in_percent),2)])

        return(outdata)
#Logic Starts here

connect = Alpaca()

#print(connect.history('VXRT,TSLA','day','7'))

#Volatility Data
#volatility_7d = connect.volatility(['TSLA','VXRT'],'day','7')

#print(volatility_7d)

#Avg High/Low num data. 
avg_low_7d = connect.avgLow(['VXRT','TSLA'],'day','7')
avg_high_7d = connect.avgHigh(['VXRT','TSLA'],'day','7')

print(avg_low_7d)
print(avg_high_7d)
