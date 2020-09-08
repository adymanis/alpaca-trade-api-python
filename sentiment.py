from nltk.sentiment.vader import SentimentIntensityAnalyzer
import nltk


class Sentiment:

    def __init__(self):   
        nltk.download('vader_lexicon')
        return

    def get_sentiment_score(self,sentence):      
        sid_obj = SentimentIntensityAnalyzer() 
        sentiment_dict = sid_obj.polarity_scores(sentence) 
        #print(sentiment_dict)
        return(round(sentiment_dict['compound'],6)) 