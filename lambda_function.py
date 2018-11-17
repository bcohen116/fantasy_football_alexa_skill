import urllib.request
import json
from ask_sdk_model.ui import AskForPermissionsConsentCard
from ask_sdk_model.services import ServiceException
from ask_sdk_core.handler_input import HandlerInput
import matchup_scores
import player_scores
import boto3
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key, Attr

# dynamodb = boto3.client('dynamodb')
dynamodb = boto3.resource('dynamodb')
alexaUserId = ""

#Main method, runs every time an intent is called from Alexa
def lambda_handler(event, context):
    if event["session"]["new"]:
        on_session_started({"requestId": event["request"]["requestId"]}, event["session"])
        global alexaUserId
        alexaUserId = event['session']['user']['userId']
        print("Found user ID from json: " + alexaUserId)

    if event["request"]["type"] == "LaunchRequest":
        return on_launch(event["request"], event["session"])
    elif event["request"]["type"] == "IntentRequest":
        return on_intent(event["request"], event["session"])
    elif event["request"]["type"] == "SessionEndedRequest":
        return on_session_ended(event["request"], event["session"])

def on_session_started(session_started_request, session):
    print ("Starting new session.")


def on_launch(launch_request, session):
    return get_welcome_response()

#Handle what the user said
def on_intent(intent_request, session):
    intent = intent_request["intent"]
    intent_name = intent_request["intent"]["name"]

    if intent_name == "get_player_score":
        return player_scores.get_player_score(intent_request)
    elif intent_name == "check_matchup_score":
        return matchup_scores.getTeamId(intent_request,alexaUserId,session)
    elif intent_name == "check_matchup_projections":
        return matchup_scores.getTeamId(intent_request,alexaUserId,session)
    elif intent_name == "AMAZON.HelpIntent":
        return get_welcome_response()
    elif intent_name == "AMAZON.CancelIntent" or intent_name == "AMAZON.StopIntent":
        return handle_session_end_request()
    else:
        raise ValueError("Invalid intent")

def on_session_ended(session_ended_request, session):
    print ("Ending session.")
    # TODO Cleanup goes here...

def handle_session_end_request():
    card_title = "Thanks"
    speech_output = "LOL, you're going to lose."
    should_end_session = True

    return build_response({}, build_speechlet_response(card_title, speech_output, None, should_end_session))

def get_welcome_response():
    #Check if this is a first time setup
    table = dynamodb.Table('fantasy_football_names')
    teamId = ""
    if (alexaUserId != ""):
        try:
            response = table.query(
                IndexName='alexaUserID-index',
                KeyConditionExpression=Key('alexaUserID').eq(alexaUserId)
            )
        except ClientError as e:
            #Did not find user id in database, save it later inside matchup_scores
            print(e.response['Error']['Message'])
            
        else:
            #Success, found matching user id's, continue with the program
            for i in response['Items']:
                print("Saved alexa ID is: " + i['alexaUserID'])
                teamId = i['teamId']
                
    #Save the teamId to the session attributes which can be parsed out later by methods needing to have specific team info
    session_attributes = {'teamId':teamId}
    
    #Create response to Alexa
    card_title = "Fantasy Football"
    speech_output = "Welcome to the Alexa ESPN Fantasy Football skill. " \
                    "You can ask me for player scores, matchup scores, or statistics. "
    reprompt_text = "Please ask me for fantasy football information, " \
                    "for example How is my team doing?"
    should_end_session = False
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))

#Build responses to Alexa
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