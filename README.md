# fantasy_football_alexa_skill
Allows for commands using Alexa like:
* How is Drew Brees doing today?
  * Gives Individual player point values
* Check my matchup
  * Gives the current matchup score for this week
* What are my projections?
  * Gives the projected matchup score for this week

... and many more

Uses Python 3.6 with AWS Lambda Functions as well as the Alexa Skill Builder
Lambda Functions are used to full JSON data from the ESPN public API to retrieve player and team data.
lambda_function.py is set up in my lambda console to run upon Alexa skill invocation. intent_schema.json is the template for the custom alexa skill intents.


Due to the Terms of the ESPN API, this app must be free to use. I made this purely for educational and personal use and is not meant to be used commercially.
