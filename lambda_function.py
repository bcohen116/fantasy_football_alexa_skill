import urllib.request
import json
from ask_sdk_core.skill_builder import CustomSkillBuilder
from ask_sdk_core.api_client import DefaultApiClient
from ask_sdk_core.dispatch_components import AbstractRequestHandler
from ask_sdk_core.dispatch_components import AbstractExceptionHandler
from ask_sdk_core.utils import is_request_type, is_intent_name
from ask_sdk_model.ui import AskForPermissionsConsentCard
from ask_sdk_model.services import ServiceException
import matchup_scores
import player_scores

#Variables
USERNAME = ""
ALEXA_SKILL_ID = "hidden, contact me to get this"
#sb will allow us to use the AbstractRequestHandlers
sb = CustomSkillBuilder(api_client=DefaultApiClient())
permissions = ["alexa::profile:name:read"]

#Speech strings to send back to Alexa to say
API_FAILURE = ("There was an error with the Device Address API. Please try again.")
NO_PERMISSIONS = ("You have not given this skill permissions. Open the Alexa App.")
REPROMPT_PERMISSIONS = ("Open the Alexa App and click on the card to enable permissions.")
NOT_SUPPORTED = ("That command is not supported, ask something else.")
WELCOME_REPROMPT = ("Please ask me for fantasy football information, "
                    "for example How is my team doing?")
WELCOME = ("Welcome to the Alexa ESPN Fantasy Football skill. "
            "You can ask me for player scores, matchup scores, or statistics.")
SESSION_END = ("LOL, you're going to lose.")

#Handle intents from the alexa skill to check stats of a single player
class CheckPlayerStatsIntentHandler(AbstractRequestHandler):
    #Check intent name
    def can_handle(self, handler_input):
        return is_intent_name("check_player_stats")(handler_input)

    #If intent name was correct, this method will run
    def handle(self, handler_input):
        return player_scores.get_player_score(handler_input)

#Handle intents from the alexa skill to check matchup scores for the current week
class MatchupScoresIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_intent_name("check_matchup_score")(handler_input)

    def handle(self, handler_input):
        return matchup_scores.get_matchup_score()

class SessionEndedRequestHandler(AbstractRequestHandler):
    # Handler for Session End
    def can_handle(self, handler_input):
        return is_request_type("SessionEndedRequest")(handler_input)

    def handle(self, handler_input):
        # return on_session_ended()
        return handler_input.response_builder.response

class HelpIntentHandler(AbstractRequestHandler):
    # Handler for Help Intent
    def can_handle(self, handler_input):
        return is_intent_name("AMAZON.HelpIntent")(handler_input)

    def handle(self, handler_input):
        return get_welcome_response()


class CancelOrStopIntentHandler(AbstractRequestHandler):
    # Single handler for Cancel and Stop Intent
    def can_handle(self, handler_input):
        return (is_intent_name("AMAZON.CancelIntent")(handler_input) or
                is_intent_name("AMAZON.StopIntent")(handler_input))

    def handle(self, handler_input):
        return handle_session_end_request()


class FallbackIntentHandler(AbstractRequestHandler):
    # AMAZON.FallbackIntent is only available in en-US locale.
    # This handler will not be triggered except in that locale,
    # so it is safe to deploy on any locale
    def can_handle(self, handler_input):
        return is_intent_name("AMAZON.FallbackIntent")(handler_input)

    def handle(self, handler_input):
        handler_input.response_builder.speak(NOT_SUPPORTED).ask(WELCOME_REPROMPT)
        return handler_input.response_builder.response

def on_session_ended(session_ended_request, session):
    print ("Ending session.")
    # TODO Cleanup goes here...

def handle_session_end_request():
    card_title = "Thanks"
    speech_output = SESSION_END
    should_end_session = True

    return build_response({}, build_speechlet_response(card_title, speech_output, None, should_end_session))

def get_welcome_response():
    session_attributes = {}
    card_title = "Fantasy Football"
    speech_output = WELCOME
    reprompt_text = WELCOME_REPROMPT
    should_end_session = False
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))

#When the Alexa app launches, this will activate
class NameRequestHandler(AbstractRequestHandler):
    # Handler for getting user name out of the Alexa account info
    def can_handle(self, handler_input):
        #Run on LaunchRequest so it gets the username on startup
        return is_request_type("LaunchRequest")(handler_input)

    #If the request type above returna true, this handle will run
    def handle(self, handler_input):
        req_envelope = handler_input.request_envelope
        ups_service = handler_input.service_client_factory.get_ups_service()
        # print("Request envelope: {}".format(req_envelope))
        print("Request envelope: {}".format(req_envelope.session.application.application_id))
        appId = req_envelope.session.application.application_id
        #Check to make sure only the fantasy football alexa skill is calling this to prevent misuse
        if (appId != ALEXA_APP_ID):
            raise ValueError("Invalid Application ID")
        USERNAME = ups_service.get_profile_name())

        #Name was retreived and stored for later, now lets put together a welcome message:
        return get_welcome_response()

class GetPermissionExceptionHandler(AbstractExceptionHandler):
    # Custom Exception Handler for handling device address API call exceptions
    def can_handle(self, handler_input, exception):
        return isinstance(exception, ServiceException)

    def handle(self, handler_input, exception):
        if exception.status_code == 403:
            #code 403 means access denied
            handler_input.response_builder.speak(
                NO_PERMISSIONS).set_card(
                AskForPermissionsConsentCard(permissions=permissions))
        else:
            handler_input.response_builder.speak(
                ).ask(API_FAILURE)

        return handler_input.response_builder.response


class CatchAllExceptionHandler(AbstractExceptionHandler):
    # Catch all exception handler, log exception and
    # respond with custom message
    def can_handle(self, handler_input, exception):
        return True

    def handle(self, handler_input, exception):
        print("Encountered following exception: {}".format(exception))

        speech = "Sorry, there was some problem. Please try again!!"
        handler_input.response_builder.speak(speech).ask(speech)

        return handler_input.response_builder.response

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

sb.add_request_handler(CheckPlayerStatsIntentHandler())
sb.add_request_handler(MatchupScoresIntentHandler())
sb.add_request_handler(NameRequestHandler())
sb.add_request_handler(HelpIntentHandler())
sb.add_request_handler(CancelOrStopIntentHandler())
sb.add_request_handler(FallbackIntentHandler())
sb.add_request_handler(SessionEndedRequestHandler())
sb.add_exception_handler(GetPermissionExceptionHandler())
sb.add_exception_handler(CatchAllExceptionHandler())
lambda_handler = sb.lambda_handler()
