import os
import time
import re
from slackclient import SlackClient
from subprocess import check_output
import Adafruit_DHT
import pyowm

owm = pyowm.OWM('openweathermapskeyhere')

# instantiate Slack client
slack_client = SlackClient(os.environ.get('SLACK_BOT_TOKEN'))
# starterbot's user ID in Slack: value is assigned after the bot starts up
starterbot_id = None

# constants
RTM_READ_DELAY = 1 # 1 second delay between reading from RTM
EXAMPLE_COMMAND = "who is your master?"
AC_ON = "ac on"
AC_OFF = "ac off"
TEMP = "temp"
WEATHER = "weather"
MENTION_REGEX = "^<@(|[WU].+?)>(.*)"
observation = owm.weather_at_coords(41.683983, -70.081409)

def parse_bot_commands(slack_events):
    """
        Parses a list of events coming from the Slack RTM API to find bot commands.
        If a bot command is found, this function returns a tuple of command and channel.
        If its not found, then this function returns None, None.
    """
    for event in slack_events:
        if event["type"] == "message" and not "subtype" in event:
            user_id, message = parse_direct_mention(event["text"])
            if user_id == starterbot_id:
                return message, event["channel"]
    return None, None

def parse_direct_mention(message_text):
    """
        Finds a direct mention (a mention that is at the beginning) in message text
        and returns the user ID which was mentioned. If there is no direct mention, returns None
    """
    matches = re.search(MENTION_REGEX, message_text)
    # the first group contains the username, the second group contains the remaining message
    return (matches.group(1), matches.group(2).strip()) if matches else (None, None)

def handle_command(command, channel):
    """
        Executes bot command if the command is known
    """
    observation = owm.weather_at_coords(41.683983, -70.081409)
    w = observation.get_weather()
    # Default response is help text for the user
    default_response = "Not sure what you mean. Try *{}*, *{}*, *{}*, *{}*.".format(AC_ON, AC_OFF, TEMP, WEATHER)
    temperature = "no reading"
    humidity = "no reading"
    # Finds and executes the given command, filling in response
    response = None
    # This is where you start to implement more commands!
    if command.startswith(EXAMPLE_COMMAND):
        response = "Matt Desmarais aka matt8588 is my creator and master"
    if command.startswith(TEMP):
        #get dht temp/humidity
        humidity, temperature = Adafruit_DHT.read_retry(11, 4)
        #return temp and humidity in response 
        response = str(9.0/5.0 * temperature + 32)+"F "+str(humidity)+"%"
    if command.startswith(WEATHER):
        #get openweathermaps temp/humidity data
        response = "Outdoor temp/humidity: "+str(w.get_temperature('fahrenheit')["temp"])+"F/"+str(w.get_humidity())+"%"
    if command.startswith(AC_ON):
        #get dht temp/humidity
        humidity, temperature = Adafruit_DHT.read_retry(11, 4)
        #return ac on with current temp/humidity
        response = "AC on and set to max! \n"+str(9.0/5.0 * temperature + 32)+"F "+str(humidity)+"%"
        #send air conditioner on at max cool settings
        os.system("sudo irsend SEND_ONCE aircond POWER2")
    if command.startswith(AC_OFF):
        #get dht temp/humidity
        humidity, temperature = Adafruit_DHT.read_retry(11, 4)
        #return temp and humidity in response 
        response = "AC off! \n"+str(9.0/5.0 * temperature + 32)+"F "+str(humidity)+"%"
        #send air conditioner off code
        os.system("sudo irsend SEND_ONCE aircond OFF")

    # Sends the response back to the channel
    slack_client.api_call(
        "chat.postMessage",
        channel=channel,
        text=response or default_response
    )

if __name__ == "__main__":
    if slack_client.rtm_connect(with_team_state=False):
        print("Starter Bot connected and running!")
        # Read bot's user ID by calling Web API method `auth.test`
        starterbot_id = slack_client.api_call("auth.test")["user_id"]
        while True:
            command, channel = parse_bot_commands(slack_client.rtm_read())
            if command:
                handle_command(command, channel)
            time.sleep(RTM_READ_DELAY)
    else:
        print("Connection failed. Exception traceback printed above.")
