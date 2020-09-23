import alpaca_trade_api as tradeapi
import json
import statistics
import numpy as np
from ftplib import FTP
from io import BytesIO
from sentiment import Sentiment
import tweepy
import calendar
import time
from datetime import datetime, timedelta


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

    def getConfig(self,param):
    #Returns config in dictionary var
        with open('config.json') as json_file:
            config = json.load(json_file)

        return(config[param])

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
        with FTP(self.getConfig('Tune')['Nasdaq_URL']) as ftp: # use context manager to avoid
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
        with FTP(self.getConfig('Tune')['Nasdaq_URL']) as ftp: # use context manager to avoid
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

    def lasttrade(self,symbol):   
        return(self.api.get_last_trade(symbol))

    def history(self,symbols,timeframe,limit):
        #Create batches for api call of 100 max symbols API only allow ~100 symbols per request so I broke up the requests into batches 
        hist = {}
        for b in self.batch(symbols, self.getConfig('Tune')['API_Batch_Size']):
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
                if lowcalcs > self.getConfig('Tune')['Stock_Picker_Min_Price'] :

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

                    if len(changes_in_percent) > 0 and len(normalizedVols) > 0:
                        if round(statistics.mean(changes_in_percent),2) >= self.getConfig('Tune')['Stock_Picker_Min_Perc_Change'] and round(statistics.mean(normalizedVols),2) >= self.getConfig('Tune')['Stock_Picker_Min_Vol']:
                            #tweet_sent = self.get_tweet_sent(['$'+symbol],7)
                            #outdata.append([symbol,round(statistics.mean(changes_in_percent),2),round(statistics.mean(normalizedVols),2),lowcalcs,highcalcs,tweet_sent['$'+symbol]])
                            outdata.append([symbol,round(statistics.mean(changes_in_percent),2),round(statistics.mean(normalizedVols),2),lowcalcs,highcalcs])

        return(outdata)    

    def normalize(self,ar):
        #Function will remove outliers from array. Determins if numbers have deviation if so removes and returns normalized array. 
        an_array = np.array(ar)
        mean = np.mean(an_array)
        standard_deviation = np.std(an_array)
        distance_from_mean = abs(an_array - mean)
        max_deviations = self.getConfig('Tune')['Avg_Vol_Deviation']
        not_outlier = distance_from_mean < max_deviations * standard_deviation
        no_outliers = an_array[not_outlier]
        return(no_outliers)

    def get_tweet_sent(self,hashtag,time):
        #Historical twitter sentiment for time frame
        sentiment = Sentiment()
        d = datetime.today() - timedelta(days=time)

        authentication = tweepy.OAuthHandler(self.getConfig('Tweet')['consumer_key'], self.getConfig('Tweet')['consumer_secret'])
        authentication.set_access_token(self.getConfig('Tweet')['access_token'], self.getConfig('Tweet')['access_token_secret'])
        api = tweepy.API(authentication, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)

        tweetsPerQry = 100
        maxTweets = self.getConfig('Tweet')['maxTweets']
        data = {}

        for h in hashtag:
            maxId = -1
            tweetCount = 0
            sent_total = []

            while tweetCount < maxTweets:

                if (maxId < 0):
                    newTweets = api.search(q=h, count=tweetsPerQry, result_type="recent", tweet_mode="extended",languages=["en"])
                else:
                    newTweets = api.search(q=h, count=tweetsPerQry, max_id=str(maxId - 1), result_type="recent",
                                        tweet_mode="extended",languages=["en"])

                if not newTweets:
                    #print("Aint no tweet anymore....")
                    break

                for tweet in newTweets:
                    created_at = tweet.created_at
                    text = tweet.full_text
                    sentiment_score = sentiment.get_sentiment_score(text) 
                    followers = 0
                    #Remove scores of zero and only add for date
                    if created_at >= d and sentiment_score != 0:
                        sent_total.append(sentiment_score)
                        

                tweetCount += len(newTweets)
                #print(h, tweetCount)
                maxId = newTweets[-1].id
            #This seems to be more acurate with median than mean
            data[h] = round(statistics.median(sent_total),3)
                #print(maxId)
        return(data)
 
                
