#from twython import TwythonStreamer
import tweepy
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import nltk
import sqlite3
import asyncio
import sys
import time
import calendar
import json
from influxdb import InfluxDBClient

nltk.download('vader_lexicon')

class MyStreamListener(tweepy.StreamListener):
    def get_config(self):
        with open('config.json') as json_file:
            config = json.load(json_file)
           
            consumer_key = config['Tweet']['consumer_key']
            consumer_secret = config['Tweet']['consumer_secret']
            access_token = config['Tweet']['access_token']
            access_token_secret = config['Tweet']['access_token_secret']
            maxTweets = config['Tweet']['maxTweets']

        return({'consumer_key': consumer_key,'consumer_secret': consumer_secret, 'access_token': access_token, 'access_token_secret': access_token_secret, 'maxTweets': maxTweets })
    def on_status(self, status):
        #if status.text:
        tweet = status.text
        followers = status.user.followers_count
        timestamp = status.timestamp_ms
        sentiment_score = self.get_sentiment_score(tweet) 
        #print(tweet)
        #print(data['user']['friends_count'])
        if followers > 0:
            for t in track:
                if t in tweet:
                    #print("{} Followers: {} Score: {} Time: {}".format(tweet,followers,sentiment_score,timestamp))
                    self.push_to_db(t,timestamp,tweet,sentiment_score,followers)
                    self.push_to_influx(t,round(int(timestamp)),tweet,sentiment_score,followers)

                #Check if table exists before adding data
                c.execute("SELECT count(name) FROM sqlite_master WHERE type='table' AND name='{}'".format(t.replace("$","")))

                if c.fetchone()[0]==1 : 

                    #Sentiment av for past 10 min                       
                    c.execute("Select ROUND(AVG(sentiment_score),3) from {} where datetime(date/1000, 'unixepoch', 'localtime') >= datetime('now', '-10 Minute', 'localtime')".format(t.replace("$","")))
                    avgSent10min = "Sentiment 10M: "+ str(c.fetchone())

                    c.execute("Select ROUND(AVG(sentiment_score),3) from {} where datetime(date/1000, 'unixepoch', 'localtime') >= datetime('now', '-60 Minute', 'localtime')".format(t.replace("$","")))
                    avgSent1HR = "Sentiment 1HR: "+ str(c.fetchone())

                    c.execute("Select ROUND(AVG(sentiment_score),3) from {} where datetime(date/1000, 'unixepoch', 'localtime') >= datetime('now', '-720 Minute', 'localtime')".format(t.replace("$","")))
                    avgSent24HR = "Sentiment 24HR: "+ str(c.fetchone())
                    
                    c.execute("SELECT count(*) FROM {} where datetime(date/1000, 'unixepoch', 'localtime') >= datetime('now', '-1 Minute', 'localtime')".format(t.replace("$","")))
                    Tweetfreq = "Tweets/Min: " + str(c.fetchone())
                    print(t,avgSent10min,avgSent1HR,avgSent24HR,Tweetfreq)


    def get_sentiment_score(self,sentence):      
        sid_obj = SentimentIntensityAnalyzer() 
        sentiment_dict = sid_obj.polarity_scores(sentence) 
        #print(sentiment_dict)
        return(round(sentiment_dict['compound'],6)) 

    def push_to_db(self,t,timestamp,tweet,sentiment_score,followers):

        t = t.replace("$","")
        tweet = tweet.replace("'","")

        c.execute("CREATE TABLE IF NOT EXISTS {} (date text, symbol text, tweet text, sentiment_score NUMERIC, followers int)".format(t))
        c.execute("INSERT INTO {} VALUES ('{}','{}','{}','{}','{}')".format(t,timestamp,t,tweet,sentiment_score,followers))
        conn.commit()

    def push_to_influx(self,t,timestamp,tweet,sentiment_score,followers):

        t = t.replace("$","")
        tweet = tweet.replace("'","")

        json_body = [
            {
                "measurement": "sentiment",
                "tags": {
                    "ticker": t,
                },
                "time": timestamp,
                "fields": {
                    "Sentiment": sentiment_score
                }
            }
        ]
                
        Influx.write_points(json_body, time_precision='ms')

    def get_tweet_hist(self,hashtag):
        tweetsPerQry = 100
        maxTweets = self.get_config()['maxTweets']

        for h in hashtag:
            maxId = -1
            tweetCount = 0

            while tweetCount < maxTweets:

                if (maxId < 0):
                    newTweets = api.search(q=h, count=tweetsPerQry, result_type="recent", tweet_mode="extended")
                else:
                    newTweets = api.search(q=h, count=tweetsPerQry, max_id=str(maxId - 1), result_type="recent",
                                        tweet_mode="extended")

                if not newTweets:
                    print("Aint no tweet anymore....")
                    break

                for tweet in newTweets:
                    created_at = round(calendar.timegm(time.strptime(str(tweet.created_at), "%Y-%m-%d %H:%M:%S"))) * 1000
                    text = tweet.full_text
                    sentiment_score = self.get_sentiment_score(text) 
                    followers = 0

                    self.push_to_db(h,created_at,text,sentiment_score,followers)
                    self.push_to_influx(h,created_at,text,sentiment_score,followers)
                    #trainingData.append(tweet_tuple)

                tweetCount += len(newTweets)
                print(h, tweetCount)
                maxId = newTweets[-1].id
                #print(maxId)




myStreamListener = MyStreamListener()

config = myStreamListener.get_config()


#TwitterAuth
authentication = tweepy.OAuthHandler(config['consumer_key'], config['consumer_secret'])
authentication.set_access_token(config['access_token'], config['access_token_secret'])
api = tweepy.API(authentication, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)

#Connect TO DB
conn = sqlite3.connect(":memory:")
#conn = sqlite3.connect('example.db')
c = conn.cursor()

#Connect to Influx
Influx = InfluxDBClient(config['influx_server'], '8086', '', '',config['inflush_db'] )
Influx.drop_database(config['inflush_db'])
Influx.create_database(config['inflush_db'])


track = ['$TSLA','$AAPL','$AAL','$CHWY','$PTON','$CCL','$LUV','$UPS','$FDX','$JPM','$LOW','$DIS','$OSTK']
#track = ['$TSLA','$AAPL']
#track = 'apple,tesla,chewy,carnivalcruise,southwestair'

#PreLoad HistData
myStreamListener.get_tweet_hist(track)

myStream = tweepy.Stream(auth = api.auth, listener=myStreamListener)
myStream.filter(track=track)

#stream.statuses.filter(track=track,language='en',filter_level=None)
