import urllib.request
import urllib.parse
import json

leagueId = "Contact me to get this. Personal info"
seasonId = "2018"
#SWID and ESPN s2 are cookie data, replace with your personal cookie
SWID = "Contact me to get this, or use your own cookie"
ESPN_S2 = "Contact me to get this, or use your own cookie"
#list of what the "slotCategoryId" and "eligibleSlotCategoryIds" means in the boxscore API
slots = {0: 'QB', 2: 'RB', 4: 'WR', 6: 'TE',
         16: 'D/ST', 17: 'K', 20: 'BE', 23: 'FLEX'}

#Get the fantasy score for a specific player
def get_player_score(intent_request):
    # print(json.dumps(intent_request))
    playerRequested = intent_request['intent']['slots']['Player']['value']
    card_title = "Player Fantasy Score"
    reprompt_text = ""
    should_end_session = False

    #Get the current scoreboard data
    params={'leagueId': leagueId, 'seasonId': seasonId}
    #Left out 'matchupPeriodId' to only retreive the latest week
    arguments = urllib.parse.urlencode(params)
    scoreboardInfo = urllib.request.urlopen('http://games.espn.com/ffl/api/v2/scoreboard?' + arguments)
    scoreboardInfo= scoreboardInfo.read()
    scoreboardInfo = json.loads(scoreboardInfo.decode("utf-8"))
    matchupInfo = {}

    # get all matchups for the current week
    for match in range(len(scoreboardInfo['scoreboard']['matchups'])):
        homeId = scoreboardInfo['scoreboard']['matchups'][match]['teams'][0]['team']['teamId']

        params={'leagueId': leagueId, 'seasonId': seasonId, 'teamId': homeId}
        #Left out 'matchupPeriodId' to only retreive the latest week
        arguments = urllib.parse.urlencode(params)
        cookies={'SWID': SWID, 'espn_s2': ESPN_S2}
        encodedCookies = urllib.parse.urlencode(cookies)
        boxScore = urllib.request.urlopen('http://games.espn.com/ffl/api/v2/boxscore?' + arguments + '&' + encodedCookies)

        boxScore = boxScore.read()
        data = json.loads(boxScore.decode("utf-8"))
        matchupInfo[match] = data

    speech_output = ""
    for match in range(len(matchupInfo)):
        #loop through all of the matchups to retreive a list of all players on active rosters
        homeTeam = matchupInfo[match]['boxscore']['teams'][0]['slots']
        awayTeam = matchupInfo[match]['boxscore']['teams'][1]['slots']

        #Check each player to see if we find the one the user asked for
        for count, player in enumerate(homeTeam):
            resultPlayerSpeechOutput = search_for_player(playerRequested,count,player)
            if resultPlayerSpeechOutput != "":
                #If player is found, a non-empty string will be returned
                speech_output = resultPlayerSpeechOutput
                break #Found the requested player, stop searching

        #More checking for players
        for count, player in enumerate(awayTeam):
            resultPlayerSpeechOutput = search_for_player(playerRequested,count,player)
            if resultPlayerSpeechOutput != "":
                #If player is found, a non-empty string will be returned
                speech_output = resultPlayerSpeechOutput
                break #Found the requested player, stop searching

    if speech_output == "":
        #No Player was found if this is true, tell user the search didn't work
        speech_output = "I searched for %s but did not find anything." % (playerRequested)

    return build_response(build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))

#Methods for parsing out the player data from ESPN
def search_for_player(playerRequested,count,player):
    try:
        if (playerRequested.casefold() == (player['player']['firstName'] + ' ' + player['player']['lastName']).casefold()):
            #player asked for by user is the same as the one found here
            if (player['opponentProTeamId'] == -1):
                #Player is on BYE if this is true, don't bother getting a score
                return ("" + playerRequested + " is on Bye")
            else:
                try:
                    score = player['currentPeriodRealStats']['appliedStatTotal']
                except KeyError:
                    #Player has not played yet, or no score available
                    score = 0
                return ("%s has %i points this week." % (playerRequested,score))
        else:
            return ("")
    except KeyError:
        print("No Player Entry Found in JSON")
        return ("")

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

def build_response(speechlet_response):
    return {
        "version": "1.0",
        "response": speechlet_response
    }
