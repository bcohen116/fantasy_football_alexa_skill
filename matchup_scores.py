import urllib.request
import json

leagueId = "hidden, sorry. Contact me to get this"
seasonId = "2018"

#Get the fantasy score for a specific player
def get_matchup_score():
    session_attributes = {}
    card_title = "Player Fantasy Score"
    reprompt_text = ""
    should_end_session = False

    #Retreieve matchup data from API
    result = urllib.request.urlopen('http://games.espn.com/ffl/api/v2/scoreboard?leagueId='+leagueId+'&seasonId=' + seasonId)
    resultBody = result.read()
    data = json.loads(resultBody.decode("utf-8"))

    #Sort out the data into a better format for use by Alexa
    df = []
    for key in data:
        temp = data['scoreboard']['matchups']
        for match in temp:
            df.append([key,
                       match['teams'][0]['team']['teamAbbrev'],
                       match['teams'][1]['team']['teamAbbrev'],
                       match['teams'][0]['score'],
                       match['teams'][1]['score']])
    speech_output = "Output from ESPN: " + json.dumps(df)

    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))

#Build speech model to send back to Alexa
def build_speechlet_response(title, output, reprompt_text, should_end_session):
    return {
        "outputSpeech": {
            "type": "PlainText",
            "text": output
        },
        "card": {
            "type": "Simple",
            "title": title,
            "content": output
        },
        "reprompt": {
            "outputSpeech": {
                "type": "PlainText",
                "text": reprompt_text
            }
        },
        "shouldEndSession": should_end_session
    }

def build_response(session_attributes, speechlet_response):
    return {
        "version": "1.0",
        "sessionAttributes": session_attributes,
        "response": speechlet_response
    }
