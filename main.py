import alpaca_trade_api as tradeapi
import json
import statistics
import pandas as pd
import numpy as np

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

    def getConfig(self):
    #Returns config in dictionary var
        with open('config.json') as json_file:
            config = json.load(json_file)

        return(config['Tune'])
        
    def account(self):   
        return(self.api.get_account())

    def lastquote(self,symbol):   
        return(self.api.get_last_quote(symbol))

    def history(self,symbols,timeframe,limit):   
        return(self.api.get_barset(symbols,timeframe,limit))

    def avgLow(self,symbols,timeframe,limit):
        #Get average low over period of time
        histdata = self.history(symbols,timeframe,limit)
        outdata = {}

        for symbol in symbols:
            lows = []
            for d in histdata[symbol]:
                lows.append(d.l)
            outdata.update({symbol:round(statistics.mean(lows),2)})

        return(outdata)

    def avgHigh(self,symbols,timeframe,limit):
        #Get average high over period of time
        histdata = self.history(symbols,timeframe,limit)
        outdata = {}

        for symbol in symbols:
            highs = []
            for d in histdata[symbol]:
                highs.append(d.h)
            outdata.update({symbol:round(statistics.mean(highs),2)})

        return(outdata)

    def avgVol(self,symbols,timeframe,limit):
        #Get average volume over period of time
        histdata = self.history(symbols,timeframe,limit)
        outdata = {}

        for symbol in symbols:
            vols = []
            for d in histdata[symbol]:
                vols.append(d.v)
            outdata.update({symbol:round(statistics.mean(vols))})

        return(outdata)

    def Good_Buy_Price(self,symbols,timeframe,limit):
        #This Function uses the following logic
        #   -Get Average Volume days for given timeframe
        #   -Normalize Volume for days (This removed days which either really low or high volume)
        #   -Calculate Average low for days with average volume in given timeframe

        histdata = self.history(symbols,timeframe,limit)
        outdata = []

        for symbol in symbols:
            vol = []
            lows = []
            #Compile all volumes for a given symbol to array
            for d in histdata[symbol]:
                vol.append(d.v)
            #Remove outliers from Volumes
            normalizedVols = self.normalize(vol)

            for d in histdata[symbol]:
                #If Volume exists in normalized data then use it to cal Average low. 
                if d.v in normalizedVols:
                    lows.append(d.l)
   
            outdata.append([symbol,round(statistics.mean(lows),2)])

        return(outdata)
        
    def volatility(self,symbols,timeframe,limit):
        #get % of flux, high/low based on timeframe and snapshot period
        #ie: show average daily fluctuation in price over 5 days. or do hourly fluctionation over 2 days. 
        #MATH: https://www.skillsyouneed.com/num/percent-change.html
        histdata = self.history(symbols,timeframe,limit)
        outdata = []
        for symbol in symbols:
            changes_in_percent = []
            vol = []
             #Compile all volumes for a given symbol to array
            for d in histdata[symbol]:
                vol.append(d.v)
            #Remove outliers from Volumes
            normalizedVols = self.normalize(vol)

            for d in histdata[symbol]:
                #print('Sym ',symbol)
                #print('Low ',d.l)
                #print('High' ,d.h)
                if d.v in normalizedVols:
                    changes_in_percent.append(round(((d.h - d.l)/d.l) * 100,2))
            outdata.append([symbol,round(statistics.mean(changes_in_percent),2)])

        return(outdata)

    def normalize(self,ar):
        #Function will remove outliers from array. Determins if numbers have deviation if so removes and returns normalized array. 
        an_array = np.array(ar)
        mean = np.mean(an_array)
        standard_deviation = np.std(an_array)
        distance_from_mean = abs(an_array - mean)
        max_deviations = self.getConfig()['Avg_Vol_Deviation']
        not_outlier = distance_from_mean < max_deviations * standard_deviation
        no_outliers = an_array[not_outlier]
        return(no_outliers)
                
#Logic Starts here

connect = Alpaca()

#print(connect.history('AMD','day','7'))

#Volatility Data
volatility_7d = connect.volatility(['HX'],'day','10')
print(volatility_7d)

#Avg High/Low num data. 
#avg_low_7d = connect.avgLow(['AMD'],'day','7')
#avg_high_7d = connect.avgHigh(['VXRT','TSLA','AMD'],'day','7')
#avg_vol_7d = connect.avgVol(['VXRT'],'day','5')
#gb = connect.Good_Buy_Price(['PTON','AAL','JPM','UPS','CHWY','FDX','APHA','DIS','MAR','VXRT'],'day','7')

#print(avg_low_7d)
#print(avg_high_7d)
#print(avg_vol_7d)
#print(gb)


#-Calc only avg vol days. Calc devation from avg volume  
#Cal Variation in price $
#Close sell at end of day if up a tiny amount.