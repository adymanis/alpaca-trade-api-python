import alpaca_trade_api as tradeapi
import json


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

    def averageflux(self,symbol,timeframe,limit):
        #get % of flux, high/low based on timeframe and snapshot period
        #ie: show average daily fluctuation in price over 5 days. or do hourly fluctionation over 2 days. 
        return('nothing')


#Logic Starts here
connect = Alpaca()

#connect.account()

#connect.quote('VXRT')

barset = connect.history('VXRT','day','5')

print(barset['VXRT'][0])
