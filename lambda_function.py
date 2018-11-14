import urllib.request
import json
from ask_sdk_model.ui import AskForPermissionsConsentCard
from ask_sdk_model.services import ServiceException
from ask_sdk_core.handler_input import HandlerInput
import matchup_scores
import player_scores

ALEXA_SKILL_ID = "hidden, contact me to get this"

def lambda_handler(event, context):

    #Check to make sure only the fantasy football alexa skill is calling this to prevent misuse
    if (event['session']['application']['applicationId'] != ALEXA_SKILL_ID):
        raise ValueError("Invalid Application ID")

    if event["session"]["new"]:
        on_session_started({"requestId": event["request"]["requestId"]}, event["session"])
        permissions = None
        try:
            permissions = event["session"]["user"]["permissions"]
        except KeyError:
            print("No Permissions found, asking for them in the Alexa app")
            # getPermissionsResponse()
        except Exception as err:
            raise err

        if (permissions is None):
            print("The user hasn't authorized the skill. Sending a permissions card.")
            # return getPermissionsResponse()

    if event["request"]["type"] == "LaunchRequest":
        return on_launch(event["request"], event["session"])
    elif event["request"]["type"] == "IntentRequest":
        # print(context.request_envelope.request.get_player_score())
        return on_intent(event["request"], event["session"])
    elif event["request"]["type"] == "SessionEndedRequest":
        return on_session_ended(event["request"], event["session"])

def on_session_started(session_started_request, session):
    print ("Starting new session.")

def getPermissionsResponse():
    speech_output = "You have not given this skill permissions. Open the Alexa App."

    session_attributes = {}
    reprompt_text = "Open the Alexa App and click on the card to enable permissions."
    should_end_session = False
    return build_response(session_attributes, build_permissions_response(
        speech_output, reprompt_text, should_end_session))


def on_launch(launch_request, session):
    return get_welcome_response()

#Handle what the user said
def on_intent(intent_request, session):
    intent = intent_request["intent"]
    intent_name = intent_request["intent"]["name"]

    if intent_name == "check_player_stats":
        return player_scores.get_player_score(intent_request)
    elif intent_name == "check_matchup_score":
        return matchup_scores.get_matchup_score()
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
    session_attributes = {}
    card_title = "Fantasy Football"
    speech_output = "Welcome to the Alexa ESPN Fantasy Football skill. " \
                    "You can ask me for player scores, matchup scores, or statistics. "
    reprompt_text = "Please ask me for fantasy football information, " \
                    "for example How is my team doing?"
    should_end_session = False
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))


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

#Ask for permissions
def build_permissions_response(output, reprompt_text, should_end_session):
    return {
        "outputSpeech": {
            "type": "PlainText",
            "text": output
        },
       "card": {
          "type": "AskForPermissionsConsent",
          "permissions": [
            "alexa::profile:name:read"
          ]
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
