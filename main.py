from alpaca import Alpaca
from price_forcast import prediction_model





#Logic Starts here
days = 30
connect = Alpaca()
tickers = ['APA']
#tickers = connect.get_all_syms()
histdata = connect.history(tickers,'day',str(days))

print(prediction_model(histdata,days))

#Get nasdaq Lists

#print(connect.history('AMD','day',7))

#Volatility Data

#Stock_Picker = connect.Stock_Picker(all,'day',7)

#for v in Stock_Picker:
#    print(str(v).replace("]", "").replace("[", "").replace("'", ""))

    
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