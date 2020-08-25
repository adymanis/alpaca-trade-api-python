import alpaca_trade_api as tradeapi
import json
import statistics
import pandas as pd
import numpy as np
from ftplib import FTP
from io import BytesIO

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

    def batch(self,iterable, n=1):
        #Creates batches for data 
        l = len(iterable)
        for ndx in range(0, l, n):
            yield iterable[ndx:min(ndx + n, l)]
        
    def account(self):   
        return(self.api.get_account())

    def get_all_syms(self):
        #All Syms
        nasdaq = self.get_all_syms_nasdaq()
        nyse = self.get_all_syms_nyse()
        all = nasdaq + nyse
        return(all)

    def get_all_syms_nyse(self):   
        #Pull all symbols directly from NASDAQ FTP
        data = BytesIO()
        with FTP(self.getConfig()['Nasdaq_URL']) as ftp: # use context manager to avoid
            ftp.login()                          # leaving connection open by mistake
            ftp.retrbinary("RETR /SymbolDirectory/otherlisted.txt", data.write)
        data.seek(0) # need to go back to the beginning to get content
        nyse_data = data.read().decode() # convert bytes back to string
        ftp.close()
    
        n = nyse_data.split('\r\n')[1:-2]
        all_syms_nyse = []

        for i in n:
            s = i.split('|')
            if not "$" in s[0] and not "." in s[0]:
                all_syms_nyse.append(s[0])

        return(all_syms_nyse)

    def get_all_syms_nasdaq(self):   
        #Pull all symbols directly from NASDAQ FTP
        data = BytesIO()
        with FTP(self.getConfig()['Nasdaq_URL']) as ftp: # use context manager to avoid
            ftp.login()                          # leaving connection open by mistake
            ftp.retrbinary("RETR /SymbolDirectory/nasdaqlisted.txt", data.write)
        data.seek(0) # need to go back to the beginning to get content
        nasdaq_data = data.read().decode() # convert bytes back to string
        ftp.close()

        n = nasdaq_data.split('\r\n')[1:-2]
        all_syms_nasdaq = []

        for i in n:
            s = i.split('|')
            all_syms_nasdaq.append(s[0])

        return(all_syms_nasdaq)

    def lastquote(self,symbol):   
        return(self.api.get_last_quote(symbol))

    def history(self,symbols,timeframe,limit):
        #Create batches for api call of 100 max symbols API only allow ~100 symbols per request so I broke up the requests into batches 
        hist = {}
        for b in self.batch(symbols, self.getConfig()['API_Batch_Size']):
            data = self.api.get_barset(b,timeframe,limit)
            hist.update(data)

        return(hist)

    def avgLow(self,symbols,timeframe,limit):
        #Get average low over period of time
        histdata = self.history(symbols,timeframe,limit)
        outdata = {}

        for symbol in symbols:
            lows = []
            if len(histdata[symbol]) >= limit:
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
            if len(histdata[symbol]) >= limit:
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
            if len(histdata[symbol]) >= limit:
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
            if len(histdata[symbol]) >= limit:
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
        
    def Good_Sell_Price(self,symbols,timeframe,limit):
        #This Function uses the following logic
        #   -Get Average Volume days for given timeframe
        #   -Normalize Volume for days (This removed days which either really low or high volume)
        #   -Calculate Average low for days with average volume in given timeframe

        histdata = self.history(symbols,timeframe,limit)
        outdata = []

        for symbol in symbols:
            vol = []
            lows = []
            if len(histdata[symbol]) >= limit:
                #Compile all volumes for a given symbol to array
                for d in histdata[symbol]:
                    vol.append(d.v)
                #Remove outliers from Volumes
                normalizedVols = self.normalize(vol)

                for d in histdata[symbol]:
                    #If Volume exists in normalized data then use it to cal Average low. 
                    if d.v in normalizedVols:
                        lows.append(d.h)
    
                outdata.append([symbol,round(statistics.mean(lows),2)])

        return(outdata)

    def Price_volatility(self,symbols,timeframe,limit):
        #get % of flux, high/low based on timeframe and snapshot period
        #ie: show average daily fluctuation in price over 5 days. or do hourly fluctionation over 2 days. 
        #MATH: https://www.skillsyouneed.com/num/percent-change.html
        histdata = self.history(symbols,timeframe,limit)
        outdata = []
        for symbol in symbols:
            changes_in_percent = []
            vol = []
            if len(histdata[symbol]) >= limit:
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

    def Stock_Picker(self,symbols,timeframe,limit):
        #Pass Large list to this function to do analysis on if stock is a solid buy. 
        #Checks also mini price based on config threshhold.

        #get % of flux, high/low based on timeframe and snapshot period
        #ie: show average daily fluctuation in price over 5 days. or do hourly fluctionation over 2 days. 
        #
        #MATH: https://www.skillsyouneed.com/num/percent-change.html
        histdata = self.history(symbols,timeframe,limit)
        outdata = []
        for symbol in symbols:
            changes_in_percent = []
            vol = []

            #####
            if len(histdata[symbol]) >= limit:

                #Same logic as avgLow function, I didnt want to hit API again since we already have hist data here. 
                lows = []
                highs = []
                
                for d in histdata[symbol]:
                    lows.append(d.l)
                lowcalcs = (round(statistics.mean(lows),2))

                for d in histdata[symbol]:
                    highs.append(d.h)
                highcalcs = (round(statistics.mean(highs),2))
                ##########
                #Set threshold for cheap stocks.. remove penny stocks
                if lowcalcs > self.getConfig()['Stock_Picker_Min_Price'] :

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
                    #Append only stocks which have min % in change and volume greate than
                    if round(statistics.mean(changes_in_percent),2) >= self.getConfig()['Stock_Picker_Min_Perc_Change'] and round(statistics.mean(normalizedVols),2) >= self.getConfig()['Stock_Picker_Min_Vol']:
                        outdata.append([symbol,round(statistics.mean(changes_in_percent),2),round(statistics.mean(normalizedVols),2),lowcalcs,highcalcs])

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

nasdaq = connect.get_all_syms_nasdaq()
nyse = connect.get_all_syms_nyse()
all = connect.get_all_syms()
#Get nasdaq Lists

#print(connect.history('AMD','day',7))

#Volatility Data

Stock_Picker = connect.Stock_Picker(all,'day',7)

for v in Stock_Picker:
    print(str(v).replace("]", "").replace("[", "").replace("'", ""))

#Avg High/Low num data. 

#avg_high_7d = connect.Good_Buy_Price(['BFRA'],'day',5)
#avg_vol_7d = connect.avgVol(['VXRT'],'day','5')

#gb = connect.Good_Buy_Price(['PTON','AAL','JPM','UPS','CHWY','FDX','APHA','DIS','MAR','VXRT'],'day',7)
#gs = connect.Good_Sell_Price(['PTON','AAL','JPM','UPS','CHWY','FDX','APHA','DIS','MAR','VXRT'],'day',7)

#print(avg_high_7d)
#print(avg_vol_7d)
#print(gb)
#print(gs)


#histdata = connect.history(['AMD'],'day','7')
#print(histdata)


#avg_low_7d = connect.avgLow(nasdaq,'day','7')
#print(len(avg_low_7d))





#-Calc only avg vol days. Calc devation from avg volume  
#Cal Variation in price $
#Close sell at end of day if up a tiny amount.
#Find days with same price and volume check flux
#Timing of Earnings 