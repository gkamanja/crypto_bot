'''bot designed to get input in form of start date,end date and name of coin
	then output agrph of the coin's trend as well as csv file of the info.
	Operation of the bot:
	1. enter '/start' command
	2. get message,'Welcome to crypto_bot. Please enter below the start date, end date 
		and name of coin in that order. Format of the dates should be YYYYmmdd'
	3. enter the info
	4. receive info.download graph and csv file
	5. enter info for new coin
	6. enter '/stop' command to stop the bot.
	7. receive message,'Thank you for using crypto_bot.'
'''

import requests
import json
import urllib,base64
import time
import io
from bs4 import BeautifulSoup
import csv
import sys
import seaborn as sns
from datetime import datetime
#modules for the plot
import pandas
import matplotlib.pyplot as plt


TOKEN = "API_TOKEN"
URL = "https://api.telegram.org/bot{}/".format(TOKEN)

def get_url(url):
	response = requests.get(url)
	content = response.content.decode('utf8')
	return content

def get_json_from_url(url):
	content = get_url(url)
	js = json.loads(content)
	return js

def get_updates(offset = None):
	url = URL + 'getUpdates?timeout=100'
	if offset:
		url += '&offset={}'.format(offset)
	js = get_json_from_url(url)
	return js

def get_last_chat_id_and_text(updates):
	num_updates = len(updates['result'])
	last_update = num_updates - 1
	text = updates['result'][last_update]['message']['text']
	chat_id = updates['result'][last_update]['message']['chat']['id']
	return(text,chat_id)

	#create gragh class and call it here
	#parse returned text to obtain start and end date and name of coin
def splitting_consumer_input(updates):
	text = get_last_chat_id_and_text(updates)[0]
	#text,_ = get_last_chat_id_and_text(updates)	alternative for getting only text
	input_list = text.split()
	startdate = input_list[0]
	enddate = input_list[1]
	coin = input_list[2]
	return startdate,enddate,coin

##### coin search and graphing code################
def CoinNames():
	names = []
	response = requests.get("https://api.coinmarketcap.com/v1/ticker/?limit=0")
	respJSON = json.loads(response.text)
	for i in respJSON:
		names.append(i['id'])
	return names

def gather(startdate, enddate, names):
    historicaldata = []
    counter = 1

    if len(names) == 0:
        names = CoinNames()

    for coin in names:
        r  = requests.get("https://coinmarketcap.com/currencies/{0}/historical-data/?start={1}&end={2}".format(coin, startdate, enddate))
        data = r.text
        soup = BeautifulSoup(data, "html.parser")
        table = soup.find('table', attrs={ "class" : "table"})

        #Add table header to list
        if len(historicaldata) == 0:
            headers = [header.text for header in table.find_all('th')]
            headers.insert(0, "Coin")

        for row in table.find_all('tr'):
            currentrow = [val.text for val in row.find_all('td')]
            if(len(currentrow) != 0):
                currentrow.insert(0, coin)
            historicaldata.append(currentrow)

        print("Coin Counter -> " + str(counter), end='\r')
        counter += 1
    return headers, historicaldata

def _gather(startdate, enddate, updates):
    """ Scrape data off cmc"""

    if(len(splitting_consumer_input(updates)) == 3):
        names =  [splitting_consumer_input(updates)[2]]#CoinNames()
        '''
    else:
        names = [splitting_consumer_input(updates)[2]]
        '''

    headers, historicaldata = gather(startdate, enddate, names)

    Save(headers, historicaldata,updates)

def Save(headers, rows, updates):

    if(len(splitting_consumer_input(updates)) == 3):
    	FILE_NAME = splitting_consumer_input(updates)[2] + ".csv"

    with open(FILE_NAME,'w') as f:
    	writer = csv.writer(f)
    	writer.writerow(headers)
    	writer.writerows(row for row in rows if row)
    return f
    #print("Finished!")

''' plot trend of cryptocurrency 
    #amount against date 
    #plot graphs of openning,closing and highest amount for any particular date'''

#combined line graph
def date_difference(startdate,enddate):
	date_format = "%Y-%m-%d"
	sdate = datetime(year=int(startdate[0:4]), month=int(startdate[4:6]), day=int(startdate[6:8])).strftime(date_format)
	edate = datetime(year=int(enddate[0:4]), month=int(enddate[4:6]), day=int(enddate[6:8])).strftime(date_format)
	a = datetime.strptime(sdate,date_format)
	b = datetime.strptime(edate,date_format)
	delta = b-a
	difference = delta.days+1

	return difference

def graph(startdate,enddate,updates,coin):
	sdate= 1
	edate= date_difference(startdate,enddate)
	f = open('{}.csv'.format(splitting_consumer_input(updates)[2]),'r')
	#f = open('csv_file','r')
	readfile = csv.reader(f,delimiter = ',')
	next(readfile,None)	#skips first row which contains headings
	opening = []
	closing = []
	highest = []
	lowest = []
	for row in reversed(list(readfile)):	#reversed(list(readfile)) reverses how the csv file is read:bottom to top
		opening_price = float(row[2])
		opening.append(opening_price)
		closing_price = float(row[5])
		closing.append(closing_price)
		highest_price = float(row[3])
		highest.append(highest_price)
		lowest_price = float(row[4])
		lowest.append(lowest_price)
	year = range(sdate,edate+1)

	sns.set(style='whitegrid')
	sns.set_color_codes('pastel')
	fig,ax = plt.subplots(figsize=(12,6))
	#ax = fig.axes
	ax.plot(year,opening,label = 'opening price', color ='r')
	ax.plot(year,closing, label ='closing price', color ='b')
	ax.plot(year,highest, label = 'highest price', color ='g')
	ax.plot(year, lowest, label = 'lowest price', color = 'orange')

	plt.xlim(sdate,edate)
	ax.set_ylabel('Amount in USD')
	ax.set_xlabel('Date')
	ax.set_title('Price trend of {}'.format(coin))
	legend = plt.legend(loc='upper left',bbox_to_anchor=(1,0.5),frameon=True,borderpad=1,borderaxespad=1)

	#plt.show()
	fig.savefig('crypto.jpg',dpi = fig.dpi)
	'''
	buf = io.BytesIO()
	fig.savefig(buf,format='jpeg')
	buf.seek(0)
	string = base64.b64encode(buf.read())
	return string
	'''

################################################################


def get_last_update_id(updates):
	update_ids = []
	for update in updates['result']:
		update_ids.append(int(update['update_id']))
	return max(update_ids)
	
def send_message(photo,chat_id):
	#photo = urllib.parse.quote_plus(photo)
	url = URL + "sendPhoto?chat_id={}".format(chat_id)
	r = requests.post(url,files=photo)
	#get_url(url)


def main():
	last_update_id = None
	while True:
		updates = get_updates(last_update_id)
		if len(updates['result']) > 0:
			last_update_id = get_last_update_id(updates) + 1
			startdate = splitting_consumer_input(updates)[0]
			enddate = splitting_consumer_input(updates)[1]
			coin = splitting_consumer_input(updates)[2]
			'''
			print(startdate)
			print(enddate)
			print(coin)
			print('finished')
			'''
			_gather(startdate,enddate,updates)
			graph(startdate,enddate,updates,coin)
			
			for update in updates['result']:
				chat = update['message']['chat']['id']
				#image = curl -v -F photo=@/home/gk/Desktop/BREAKnotpartofOS/Scripts/crypto.jpg
				image = {'photo':open('crypto.jpg','rb')}
				#image = graph(startdate,enddate,updates,coin)
				send_message(image,chat)
				
		time.sleep(0.5)

if __name__ == '__main__':
	main()

