from flask import Flask, request, redirect
import requests
import json
import random
import twilio.twiml
import twitter
import wolframalpha

app = Flask(__name__)

noIntent = [
    "I'm having trouble understanding you, could you rephrase your question?",
    "I didn't catch that, could you rephrase your query?",
    "Sorry, I didn't understand that. Try rephrasing your request."
]

@app.route("/", methods=['GET', 'POST'])
def recieveSMS():
    """Respond to a text with the input (this is a temporary behavior), and decide the appropriate handler"""
    wit_response = requests.get(url='https://api.wit.ai/message?v=20150912&q=' + request.values.get('Body', None),headers={'Authorization': 'Bearer I4WKESB35IVVAHPAG4YVYRQ6MB26UAGG'})
    wit_dict = json.loads(wit_response.text)
    print wit_dict
    intent = wit_dict.get('outcomes')[0].get('intent')
    print intent
    confidence = wit_dict.get('outcomes')[0].get('confidence')
    print confidence
    entities = wit_dict.get('outcomes')[0].get('entities')
    print entities

    msg = None

    if confidence < .2:
        noValidIntent()
    elif intent == "wolfram":
        msg = wolfram(entities)
    elif intent == "navigate":
        msg = navigate(entities)
    elif intent == "translate":
        msg = translate(entities)
    elif intent == "weather":
        msg = weather(entities)
    elif intent == "twitter_updates":
        msg = twitter_updates(entities)
    elif intent == "stock_report":
        msg = stock_report(entities)
    elif intent == "activities":
        msg = activities(entities)
    else:
        msg = noValidIntent()
    return str(msg)


#1 uses the wolfram alpha api to retrieve results to natural language queries.
@app.route("/wolfram", methods=['GET', 'POST'])
def wolfram(entities):
    question = entities.get('question')[0].get('value');
    client = wolframalpha.Client('Y9VVR7-5A9P7Y4893')
    res = client.query(question)
    message = next(res.results).text
    resp = twilio.twiml.Response()
    resp.message(message)
    print message
    return resp

#2 Navigate
@app.route("/navigate", methods=['GET', 'POST'])
def navigate(entities):
    key = "GSC5hkB0CEmUyk4nI2MY~HxNEzo1P1bHB1sX8EzDJpA~AmYeCHqvBerEI06DBSKWfo4pgB1w9Krgk7EH6lhGqqf3s5RaJArOzWJ-SL6AYVVw"
    origin = entities.get('origin')[0].get('value');
    destination = entities.get('destination')[0].get('value');
    bingMapsResponse = requests.get(url="http://dev.virtualearth.net/REST/V1/Routes/Driving?wp.0=" + origin + "&wp.1=" + destination + "&avoid=minimizeTolls&key="+key)
    bingMaps_dict = json.loads(bingMapsResponse.text)
    resources = bingMaps_dict.get('resourceSets')[0].get('resources')
    routeLegs = resources[0].get('routeLegs')
    message = ""
    distance = routeLegs[0].get('routeSubLegs')[0].get('travelDistance')
    message += "Total Trip Distance: " + str(distance) + " km\n"
    duration = routeLegs[0].get('routeSubLegs')[0].get('travelDuration')
    message += "Total Trip Duration: " + str(duration/60) + " min \n"
    itineraryItems = routeLegs[0].get('itineraryItems')
    count = 1
    for item in itineraryItems:
        message += str(count) + ". " + item.get('instruction').get('text') + " ("
        message += str(item.get('travelDistance')) + " km, "
        message += str(item.get('travelDuration') / 60 ) + " min)"
        message += "\n"
        count +=1
    resp = twilio.twiml.Response()
    resp.message(message)
    print message
    return resp

#3 Translate
@app.route("/translate", methods=['GET', 'POST'])
def translate(entities):
    phrase_to_translate = entities.get('phrase_to_translate')[0].get('value')
    message = ""
    if entities.get('language') == None:
        message = "Language not supported"
    else:
        language = entities.get('language')[0].get('value')
        language = language.lower()
        if language == "chinese":
            language = "zh-CHS"
        elif language == "dutch":
            language = "nl"
        elif language == "english":
            language = "en"
        elif language == "french":
            language = "fr"
        elif language == "german":
            language = "de"
        elif language == "italian":
            language = "it"
        elif language == "japanese":
            language = "ja"
        elif language == "korean":
            language = "ko"
        elif language == "portuguese":
            language = "pt"
        elif language == "russian":
            language = "ru"
        elif language == "spanish":
            language = "es"
        elif language == "swedish":
            language = "sv"
        elif language == "thai":
            language = "th"
        elif language == "vietnamese":
            language = "vi"
        else:
            message = "Language not supported"
    if message != "Language not supported":
        from microsofttranslator import Translator
        translator = Translator('SMSAssistant', 'fhV+AdYFiK0QfQ4PFys+oQ/T0xiBBVQa32kxxbP55Ks=')
        message = translator.translate(phrase_to_translate, language)
    resp = twilio.twiml.Response()
    print message
    resp.message(message)
    return resp

#4 Weather
@app.route("/weather", methods=['GET', 'POST'])
def weather(entities):
    location = entities.get('location')[0].get('value');
    weatherResponse = requests.get(url="http://api.openweathermap.org/data/2.5/weather?q=" + location)
    weather_dict = json.loads(weatherResponse.text) #Gets all the JSON
    weatherDescription = weather_dict.get('weather')[0].get('description')
    temperatureInKelvin = weather_dict.get('main').get('temp')

    temperatureInFarenheit = kelvinToFarenheit(temperatureInKelvin)
    degree_sign= u'\N{DEGREE SIGN}' #To get degree sign

    print degree_sign

    message = "In " + location + ", the weather forecast is " + weatherDescription + " and the temperature is " + str(temperatureInFarenheit) + " " + degree_sign + "F"
    resp = twilio.twiml.Response()
    resp.message(message)
    print message
    return resp

def kelvinToFarenheit(tempInK):
    return (tempInK - 273.15) * 1.8 + 32.0

#5 Twitter Updates
@app.route("/twitter_updates", methods=['GET', 'POST'])
def twitter_updates(entities):
    username = entities.get('username')[0].get('value');
    api = twitter.Api(consumer_key='4m8fjnhaub0s1KGb7jrcGZIKR',consumer_secret='rtohH46EgVGWVIA1BSEImdNpIkNqm7bvREttacwTGK72mxrLZK',access_token_key='2735117372-CEiN7lE00OBfqNmWlVmypzNkblwyVM3cpIGyYdy',access_token_secret='wgADPMZkEWEOqYCa8oZcpWdYJnOuTdtwjeJLC9JbvDew7')
    statuses = api.GetUserTimeline(screen_name=username, count =1)
    latestTweet = statuses[0].text
    message = "@"+username+": " + latestTweet
    print message
    resp = twilio.twiml.Response()
    resp.message(message)
    return resp

#6 Stock Report
@app.route("/stock_report", methods=['GET', 'POST'])
def stock_report(entities):
    company = entities.get('company')[0].get('value')
    yahooFinanceResponse = requests.get(url="http://finance.yahoo.com/webservice/v1/symbols/"+company+"/quote?format=json")
    yahooFinance_dict = json.loads(yahooFinanceResponse.text)
    price = yahooFinance_dict.get('list').get('resources')[0].get('resource').get('fields').get('price')
    message = company+" is currently at " + "$" + price +"."
    print message
    resp = twilio.twiml.Response()
    resp.message(message)
    return resp

#7 Expedia Activities
@app.route("/activities", methods=['GET', 'POST'])
def activities(entities):
    location = entities.get('location')[0].get('value')
    print location
    expediaResponse = requests.get(url="http://terminal2.expedia.com/x/activities/search?location="+location+"&apikey=yYTYKKUxJFqVXrc9fXduouBGThAAWQH5")
    expedia_dict = json.loads(expediaResponse.text)
    activities = expedia_dict.get('activities')
    message = ""
    count = 1
    for activity in activities:
        message += str(count) + ". "
        message += activity.get('title')
        message += " (" + str(activity.get('fromPrice'))
        message += " " + activity.get('fromPriceLabel') + ") \n"
        count += 1
    resp = twilio.twiml.Response()
    resp.message(message)
    print message
    return resp

# No Valid Intent Found
@app.route("/noValidIntent", methods=['GET', 'POST'])
def noValidIntent():
    resp = twilio.twiml.Response()
    message = random.choice(noIntent)
    resp.message(message)
    return resp

if __name__ == "__main__":
    app.run(debug=True)
