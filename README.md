# HaugeBot
A Twitch Bot for channel DerHauge. 

### Vote Bot
Checks every chat message for the following beginnings:

results in | trigger
--- | ---
neutral | `+-` `-+` `+/-` `-/+` `haugeNeutral`  
plus | `+` `haugePlus`  
minus | `-` `haugeMinus`  

Posts an interim result every 20 seconds and an end result after 5 seconds of no additional votes.

Checks if more than 10 votes have been added before posting any result.


### Installation

Clone this repository, create a venv and install dependencies using `pip` and the `requirements.txt`


### Configuration

Configuration of this bot is done by a `.env` use `.env.template` for reference