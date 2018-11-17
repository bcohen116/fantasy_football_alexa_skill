import urllib.request
import json
import boto3
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key, Attr

leagueId = "hidden, sorry. Contact me to get this"
seasonId = "2018"
teamId = ""
#SWID and ESPN s2 are cookie data, replace with your personal cookie
SWID = "Contact me to get this, or use your own cookie"
ESPN_S2 = "Contact me to get this, or use your own cookie"
dynamodb = boto3.resource('dynamodb')

#Get the fantasy score for a matchup
def get_matchup_score(intent_request,alexaUserId,session,attributes):
    #Initialize Variables
    global teamId
    session_attributes = attributes
    card_title = "Matchup Fantasy Score"
    reprompt_text = ""
    should_end_session = False

    #Get scoreboard data from ESPN which has matchup scores for the whole league
    result = urllib.request.urlopen('http://games.espn.com/ffl/api/v2/scoreboard?leagueId='+leagueId+'&seasonId='+ seasonId)
    resultBody = result.read()
    data = json.loads(resultBody.decode("utf-8"))
    yourScore = None
    opponentScore = None
    #Loop through all of the league matchups to find the specific user's matchup
    for key in data:
        temp = data['scoreboard']['matchups']
        for match in temp:
            #Matchups return a home and away team, so figure out which one is the user
            if match['teams'][0]['team']['teamId'] == teamId:
                #This is the user's team, now get scores
                yourScore = match['teams'][0]['score']
                yourTeamName = ""+match['teams'][0]['team']['teamLocation'] + match['teams'][0]['team']['teamNickname']
                opponentScore = match['teams'][1]['score']
                opponentTeamName = ""+match['teams'][1]['team']['teamLocation'] + match['teams'][1]['team']['teamNickname']

            elif match['teams'][1]['team']['teamId'] == teamId:
                #This is the user's team, now get scores
                yourScore = match['teams'][1]['score']
                yourTeamName = ""+match['teams'][1]['team']['teamLocation'] + match['teams'][1]['team']['teamNickname']
                opponentScore = match['teams'][0]['score']
                opponentTeamName = ""+match['teams'][0]['team']['teamLocation'] + match['teams'][0]['team']['teamNickname']

    #Put together output responses
    if yourScore is not None and opponentScore is not None:
        if yourScore > opponentScore:
            speech_output = ("You are beating " + opponentTeamName + " " + str(yourScore) + " to " + str(opponentScore))
        elif yourScore == opponentScore:
            speech_output = ("You are tied with " + opponentTeamName + " at " + str(yourScore) + " points.")
        else:
            speech_output = ("You are losing to " + opponentTeamName + " " + str(opponentScore) + " to " + str(yourScore))
    else:
        speech_output = "Your matchup was not found."

    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))

#Get matchup projections for the matchup score
def get_projection_score(intent_request,alexaUserId,session,attributes):
    #Variable initialization
    global teamId
    session_attributes = attributes
    card_title = "Matchup Fantasy Score"
    reprompt_text = ""
    should_end_session = False

    #Get boxscore data from ESPN which has projection data for matchups and players
    params={'leagueId': leagueId, 'seasonId': seasonId, 'teamId': teamId}
    #Left out 'matchupPeriodId' to only retreive the latest week
    arguments = urllib.parse.urlencode(params)
    #boxscore requires cookies to authenticate
    cookies={'SWID': SWID, 'espn_s2': ESPN_S2}
    encodedCookies = urllib.parse.urlencode(cookies)
    boxScore = urllib.request.urlopen('http://games.espn.com/ffl/api/v2/boxscore?' + arguments + '&' + encodedCookies)
    boxScore = boxScore.read()
    data = json.loads(boxScore.decode("utf-8"))

    #boxscore returns a home and away team, so find which one is the user
    if data['boxscore']['teams'][0]['teamId'] == teamId:
        #Users' team found, now get scores
        yourScore = data['boxscore']['teams'][0]['appliedActiveProjectedTotal']
        opponentScore = data['boxscore']['teams'][1]['appliedActiveProjectedTotal']
        yourTeamName = ""+data['boxscore']['teams'][0]['team']['teamLocation'] + data['boxscore']['teams'][0]['team']['teamNickname']
        opponentTeamName = ""+data['boxscore']['teams'][1]['team']['teamLocation'] + data['boxscore']['teams'][1]['team']['teamNickname']
    else:
        #Users' team found, now get scores
        yourScore = data['boxscore']['teams'][1]['appliedActiveProjectedTotal']
        opponentScore = data['boxscore']['teams'][0]['appliedActiveProjectedTotal']
        yourTeamName = ""+data['boxscore']['teams'][1]['team']['teamLocation'] + data['boxscore']['teams'][1]['team']['teamNickname']
        opponentTeamName = ""+data['boxscore']['teams'][0]['team']['teamLocation'] + data['boxscore']['teams'][0]['team']['teamNickname']

    #Construct output response
    if yourScore is not None and opponentScore is not None:
        if yourScore > opponentScore:
            speech_output = ("You are projected to beat " + opponentTeamName + " " + str(yourScore) + " to " + str(opponentScore))
        elif yourScore == opponentScore:
            speech_output = ("You are projected to tie with " + opponentTeamName + " at " + str(yourScore) + " points.")
        else:
            speech_output = ("You are projected to lose to " + opponentTeamName + " " + str(opponentScore) + " to " + str(yourScore))
    else:
        speech_output = "Your matchup was not found."

    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))

#In order to figure out what matchup data to give, we need to know the ESPN teamId of the user
def getTeamId(intent_request,alexaUserId,session):
    #Initialize Variables
    card_title = "Matchup Fantasy Score"
    reprompt_text = ""
    should_end_session = False
    global teamId
    #Check previous save data for any user data
    if 'attributes' not in session or session['attributes']['teamId'] is None or session['attributes']['teamId'] == "":
        #dialogState is used by delegate.Delegate, which determines if there are more slots from an intent that need to be filled
        if intent_request['dialogState'] == "STARTED" or intent_request['dialogState'] == "IN_PROGRESS":
            #First time user is running the app, link userId from alexa to account name
            session_attributes = {}
            should_end_session = False
            print("Getting User account name...")
            return dialog_prompt_response(session_attributes, should_end_session)

        #At this point, a name has been retreived, so now link it up with an account from my personal league
        givenName = intent_request['intent']['slots']['Name']['value']
        if (givenName.casefold() == "No names sorry, contact me to get personal info".casefold() or
                "".casefold() in givenName.casefold() or
                "".casefold() in givenName.casefold()):
            teamId = 1
        elif (givenName.casefold() == "".casefold() or
                "".casefold() in givenName.casefold()):
            teamId = 2
        elif (givenName.casefold() == "".casefold() or
                "".casefold() in givenName.casefold()):
            teamId = 3
        elif (givenName.casefold() == "".casefold() or
                "".casefold() in givenName.casefold()):
            teamId = 4
        elif (givenName.casefold() == "".casefold() or
                "".casefold() in givenName.casefold()):
            teamId = 5
        elif (givenName.casefold() == "".casefold() or
                "".casefold() in givenName.casefold()):
            teamId = 6
        elif (givenName.casefold() == "".casefold() or
                "".casefold() in givenName.casefold()):
            teamId = 7
        elif (givenName.casefold() == "".casefold() or
                "".casefold() in givenName.casefold()):
            teamId = 8
        elif (givenName.casefold() == "".casefold() or
                "".casefold() in givenName.casefold()):
            teamId = 9
        elif (givenName.casefold() == "".casefold() or
                "".casefold() in givenName.casefold() or
                "".casefold() in givenName.casefold() or
                "".casefold() in givenName.casefold()):
            teamId = 10
        else:
            card_title = "Bad user name"
            speech_output = "The name you gave me is not in the league. Restart the skill and input your name again."
            should_end_session = True
            return build_response(session_attributes, build_speechlet_response(
            card_title, speech_output, reprompt_text, should_end_session))
        session_attributes = {'Name':intent_request['intent']['slots']['Name']['value'], 'teamId':teamId}

        #Save the Alexa user id to the dynamoDb so that we do not have to keep asking the user for their name
        table = dynamodb.Table('fantasy_football_names')
        if (alexaUserId != ""):
            try:
                response = table.put_item(
                   Item={
                        'teamId': teamId,
                        'alexaUserID': alexaUserId
                    }
                )
            except ClientError as e:
                #Did not find user id in database, save it now
                print(e.response['Error']['Message'])

            else:
                #Success, found matching user id's, continue with the program
                print(json.dumps(response))
    else:
        #Previous save data was found for user data
        teamId = session['attributes']['teamId']
        session_attributes = session['attributes']

    #Check the intent so we know what score to retreive (what did the user ask)
    if intent_request['intent']['name'] == "check_matchup_score":
        return get_matchup_score(intent_request,alexaUserId,session,session_attributes)
    elif intent_request['intent']['name'] == "check_matchup_projections":
        return get_projection_score(intent_request,alexaUserId,session,session_attributes)
    else:
        card_title = "Bad Intent"
        speech_output = "Intent Error, no intent found by the name: " + intent_request['intent']['name']
        should_end_session = True
        return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))

#Build responses to send back to Alexa
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

#When a user forgets to say a Slot from an intent, we run this to ask them for more input
def dialog_prompt_response(attributes, should_end_session):
    """  create a simple json response with card """
    #Ask the User for a response
    return {
        'version': '1.0',
        'sessionAttributes': attributes,
        'response':{
            'directives': [
                {
                    'type': 'Dialog.Delegate'
                }
            ],
            'shouldEndSession': should_end_session
        }
    }
