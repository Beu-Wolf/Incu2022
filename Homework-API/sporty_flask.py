from flask import Flask, request
import requests
import json

## CONSTS WEBEX ##

bot_name = "sporty@webex.bot"
room_id = "Y2lzY29zcGFyazovL3VybjpURUFNOmV1LWNlbnRyYWwtMV9rL1JPT00vMzc4ZDg1ZjAtOTk4My0xMWVjLWI0YjYtY2YzNTNmM2E0NTMx"
auth_token = "XXXXXXXXXXXXXXXXXXX"

header_webex = {"content-type": "application/json; charset=utf-8", 
          "authorization": "Bearer " + auth_token}


## CONSTS POLYGON API

polygon_api = "XXXXXXXXXXXXXXXXXXX"
header_polygon = {"authorization": "Bearer " + polygon_api}

url_polygon = "https://api.polygon.io/"

## FLASK APP ##

app = Flask(__name__)


def human_format(num):
    num = float('{:.3g}'.format(num))
    magnitude = 0
    while abs(num) >= 1000:
        magnitude += 1
        num /= 1000.0
    return '{}{}'.format('{:f}'.format(num).rstrip('0').rstrip('.'), ['', 'K', 'M', 'B', 'T'][magnitude])


def parse_message(message: str) -> list:
    return message.strip().split()

def main_help_msg():
    return """
                Welcome to **Sporty bot**! Where you can get all the financial data you want! \n \
                List of available commands: \n \
                 - search-ticker \n \
                 - ticker-info \n \
                 - ticker-news \n \
                 - market-status
                 - help \n \
                Type a command with **help** to see more information
                """

def search_ticker(message: list) -> str:
    formatted_response = ""
    if len(message) == 1 or message[1] == "help":
        formatted_response = """
                Search for any company and get information on its tickers and primary exchange
                Usage: serch-ticker help | \<company-name\> [\<exchange\>]
                 - help : get this message
                 - company-name: name of the company to search for
                 - exchange: filter by a certain exchange
                """
    else:
        query_url = url_polygon + "v3/reference/tickers"
        q_params = {'search': message[1]}
        if len(message) == 3:
            q_params['exchange'] = message[2]
        
        
        response = requests.get(query_url, headers=header_polygon, params=q_params)
        json_response = response.json()
        
        print(json_response)

        formatted_response = f'Found **{len(json_response["results"])}** compan{"y" if len(json_response["results"]) == 1 else "ies"}:\n'
        for result in json_response["results"]:
            formatted_response += f'Ticker: {result["ticker"]}\n - Name: {result["name"]}\n - Exchange: {result["primary_exchange"]}\n\n'

    return formatted_response

def ticker_info(message: list) -> str:
    formatted_response = ""
    if len(message) != 2 or message[1] == "help":
        formatted_response = """
                Get general information about a ticker
                Usage: ticker-info help | \<ticker\>
                 - help : get this message
                 - ticker: ticker of the wanted company/asset
                """
    
    else:
        query_url = url_polygon + "v3/reference/tickers/" + message[1]
        response = requests.get(query_url, headers=header_polygon)
        json_response = response.json()

        formatted_response = ""
        if json_response["status"] == "NOT_FOUND":
            formatted_response = "Invalid Ticker! Please try again"
        else:
            formatted_response = f'Found information for {json_response["results"]["ticker"]}!\n'
            formatted_response += f'{json_response["results"]["name"]} - {json_response["results"]["description"]}\n'
            formatted_response += f' - Homepage: {json_response["results"]["homepage_url"]}\n'
            formatted_response += f' - Primary Exchange: {json_response["results"]["primary_exchange"]}\n'
            formatted_response += f' - Market Cap: {human_format(json_response["results"]["market_cap"])} {json_response["results"]["currency_name"]}\n'
            
    return formatted_response


def ticker_news(message: list) -> str:
    formatted_response = ""
    if len(message) == 1 or message[1] == "help" or len(message) > 3:
        formatted_response = """
                Get the latest news about a ticker
                Usage: ticker-news help | \<ticker\> [\<number\>]
                 - help : get this message
                 - ticker: ticker of the wanted company/asset
                 - number: Maximum number of news to get. Default is 10, maximum is 1000
                """

    else:
        query_url = url_polygon + "v2/reference/news/"
        q_params = {'ticker': message[1], 'sort': 'published_utc'}
        if len(message) == 3:
            try:
                num = int(message[2])
                q_params["limit"] = num
            except ValueError:
                formatted_response = "Invalid valiue for number of news!"
                return formatted_response

        response = requests.get(query_url, headers=header_polygon, params=q_params)
        json_response = response.json()

        formatted_response = f'Found {json_response["count"]} news article{"" if json_response["count"] == 1 else "s"}\n'
        for result in json_response["results"]:
            formatted_response += f'**{result["title"]}** published by *{result["author"]}* at {result["article_url"]}\n'
            formatted_response += f' - Description: {result["description"]}\n\n'

    return formatted_response

def market_status(message: list) -> str:
    formatted_response = ""
    if len(message) != 1:
        formatted_response = """
                            Get the current market status
                            Usage: market-status [help]
                             - help: get this message
                            """
    
    else:
        query_url = url_polygon + "v1/marketstatus/now"
        response = requests.get(query_url, headers=header_polygon)
        json_response = response.json()

        formatted_response = f'At {json_response["serverTime"]}, the market status is: {json_response["market"]}\n'
        formatted_response += f' - NASDAQ: {json_response["exchanges"]["nasdaq"]}\n'
        formatted_response += f' - NYSE: {json_response["exchanges"]["nyse"]}\n'
        formatted_response += f' - OTC: {json_response["exchanges"]["otc"]}\n\n'

        formatted_response += f'The crypto market is {json_response["currencies"]["crypto"]}\n'
        formatted_response += f'The forex market is {json_response["currencies"]["fx"]}' 

    return formatted_response


@app.route("/", methods=["GET", "POST"])
def sendMessage():
    webhook = request.json
    url = 'https://webexapis.com/v1/messages'
    msg = {"roomId": webhook["data"]["roomId"]}
    sender = webhook["data"]["personEmail"]
    message = getMessageWebex()
    message = parse_message(message)

    if (sender != bot_name):
        if (message[0] == "help"):
            msg["markdown"] = main_help_msg()

        elif (message[0] == "search-ticker"):
            msg["markdown"] = search_ticker(message)

        elif (message[0] == "ticker-info"):
            msg["markdown"] = ticker_info(message)
            
        elif (message[0] == "ticker-news"):
            msg["markdown"] = ticker_news(message)
        
        elif (message[0] == "market-status"):
            msg["markdown"] = market_status(message)
        else:
            msg["markdown"] = "Sorry! I didn't recognize that command. Type **help** to see the list of available commands."
        requests.post(url,data=json.dumps(msg), headers=header_webex, verify=True)
    
    return

def getMessageWebex():
    webhook = request.json
    url = 'https://webexapis.com/v1/messages/' + webhook["data"]["id"]
    get_msgs = requests.get(url, headers=header_webex, verify=True)
    message = get_msgs.json()['text']
    return message

app.run(debug = True)