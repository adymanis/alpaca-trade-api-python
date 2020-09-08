# Import libraries
from urllib.request import urlopen, Request
from bs4 import BeautifulSoup
import os
import pandas as pd
import matplotlib.pyplot as plt
# NLTK VADER for sentiment analysis
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import ssl 
import nltk
import collections
import datetime as dt
from scipy import stats


finwiz_url = 'https://finviz.com/quote.ashx?t='



news_tables = {}
tickers = ['AAPL']

for ticker in tickers:
    url = finwiz_url + ticker
    req = Request(url=url,headers={'user-agent': 'my-app/0.0.1'}) 
    response = urlopen(req)    
    # Read the contents of the file into 'html'
    html = BeautifulSoup(response,features="lxml")
    # Find 'news-table' in the Soup and load it into 'news_table'
    news_table = html.find(id='news-table')
    # Add the table to our dictionary
    news_tables[ticker] = news_table


parsed_news = []

# Iterate through the news
for file_name, news_table in news_tables.items():
    # Iterate through all tr tags in 'news_table'
    for x in news_table.findAll('tr'):
        # read the text from each tr tag into text
        # get text from a only
        text = x.a.get_text() 
        # splite text in the td tag into a list 
        date_scrape = x.td.text.split()
        # if the length of 'date_scrape' is 1, load 'time' as the only element

        if len(date_scrape) == 1:
            time = date_scrape[0]
            
        # else load 'date' as the 1st element and 'time' as the second    
        else:
            date = date_scrape[0]
            time = date_scrape[1]
        # Extract the ticker from the file name, get the string up to the 1st '_'  
        ticker = file_name.split('_')[0]
        
        # Append ticker, date, time and headline as a list to the 'parsed_news' list
        parsed_news.append([ticker, date, time, text])
        

nltk.downloader.download('vader_lexicon')
# Instantiate the sentiment intensity analyzer
vader = SentimentIntensityAnalyzer()

# Set column names
columns = ['ticker', 'date', 'time', 'headline']

# Convert the parsed_news list into a DataFrame called 'parsed_and_scored_news'
parsed_and_scored_news = pd.DataFrame(parsed_news, columns=columns)

# Iterate through the headlines and get the polarity scores using vader
scores = parsed_and_scored_news['headline'].apply(vader.polarity_scores).tolist()

# Convert the 'scores' list of dicts into a DataFrame
scores_df = pd.DataFrame(scores)

# Join the DataFrames of the news and the list of dicts
parsed_and_scored_news = parsed_and_scored_news.join(scores_df, rsuffix='_right')

# Convert the date column from string to datetime
parsed_and_scored_news['date'] = pd.to_datetime(parsed_and_scored_news.date).dt.date


# # Group by date and ticker columns from scored_news and calculate the mean
mean_scores = parsed_and_scored_news.groupby(['ticker','date']).mean()
print(mean_scores)

slopedata = []

for ticker, date in mean_scores.index:
    data = {'Ticker': ticker, 'Date': date, 'Score': mean_scores.loc[ticker,date]['compound']}
    slopedata.append(data)

#Convert panda data to list for analysis. Data is going to be grouped by ticker and iterated. 
grouped = collections.defaultdict(list)
for item in slopedata:
    grouped[item['Ticker']].append(item)

for s in grouped:
    slopelist = []
    for i in grouped[s]:
        data = [i['Date'],i['Score']]
        slopelist.append(data)
        
     #logic to caluclate Slope HERE
    #print(slopelist)

    df = pd.DataFrame(slopelist, columns=['date', 'value'])
    df.date =pd.to_datetime(df.date)
    df['date_ordinal'] = pd.to_datetime(df['date']).map(dt.datetime.toordinal)
    slope, intercept, r_value, p_value, std_err = stats.linregress(df['date_ordinal'], df['value'])

    print(s, round(slope * 10 , 2))



#Trend Direction
#Current Sentiment 
