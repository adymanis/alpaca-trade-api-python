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
        print(self.api.get_account())

#Logic Starts here
connect = Alpaca()

connect.account()
