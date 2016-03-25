# Twitch Translation Chat Bot
# A chat bot written in Python3 that automatically will translate your Twitch chat language for your foriegn viewers.
# 2016 - Benjamin Chu - v0.1

import sys
reload(sys)
sys.setdefaultencoding('utf-8')
import socket # imports module allowing connection to IRC
import threading # imports module allowing timing functions
import requests # imports module allowing requests
import json
import time
import calendar # imports module allowing epoch time
import ConfigParser # imports module allowing reading of .ini files
import os # for relative pathing
import string # for string manipulation
import datetime

# https://translate.yandex.net/api/v1.5/tr.json/detect ? 
# key=<API key>
#  & text=<text>
#  & [callback=<name of the callback function>]

# https://translate.yandex.net/api/v1.5/tr.json/translate ? 
# key=<API key>
#  & text=<text to translate>
#  & lang=<translation direction>
#  & [format=<text format>]
#  & [options=<translation options>]
#  & [callback=<name of the callback function>]

# =============================================
# FEATURE LIST - Add
# - Ability for users to change target language in chat
# - Static settings file
# - Commands
# - Broadcast to all function and then whisper only function
# # =============================================
# BUG LIST
# - quick successive message cause index error. need to find a way to parse out the ircdata

class APIROUTES:
	detect = 'https://translate.yandex.net/api/v1.5/tr.json/detect?key={key}&text={input}'
	translate = 'https://translate.yandex.net/api/v1.5/tr.json/translate?key={key}&text={input}&lang={target}'

# ====== READ CONFIG ======
Config = ConfigParser.ConfigParser()
Config.read(os.path.dirname(os.path.abspath(__file__)) + '/config.ini')

def ConfigSectionMap(section):
    temp_dict = {}
    options = Config.options(section)
    for option in options:
        try:
            temp_dict[option] = Config.get(section, option)
            if temp_dict[option] == -1:
                DebugPrint('skip: %s' % option)
        except:
            print('exception on %s!' % option)
            temp_dict[option] = None
    return temp_dict

# ====== CONNECTION INFO ======

# Set variables for connection
botOwner = ConfigSectionMap('settings')['botowner']
nick = ConfigSectionMap('settings')['nick']
channel = '#' + ConfigSectionMap('settings')['channel']
server = ConfigSectionMap('settings')['server']
port = int(ConfigSectionMap('settings')['port'])
password = ConfigSectionMap('settings')['oauth']
api_key = ConfigSectionMap('settings')['api']

# Translation Bot Default Settings
targetLanguage = 'ja'
filterLanguage = 'en'
broadcast = 0 # 1 for ON | 0 for OFF



# ====== IRC FUNCTIONS ======
# Extract Nickname
def getNick(data):
	nick = data.split('!')[0]
	nick = nick.replace(':', ' ')
	nick = nick.replace(' ', '')
	nick = nick.strip(' \t\n\r')
	return nick

def getMessage(data):
	if data.find('PRIVMSG') != -1:
		try:
			message = data.split(channel, 1)[1][2:]
			return message
		except IndexError:
			return 'Index Error'
		except:
			return 'No message'
	else:
		return 'Not a message'

def detectLanguage(data):
	tempDict = requests.get(APIROUTES.detect.format(key=api_key, input=data)).json()
	try:
		language = tempDict['lang']
		return str(language)
	except KeyError:
		print 'Fails gracefully, problem with detection'
		return 'Nothing'


def translateMessage(data):
	tempDict = requests.get(APIROUTES.translate.format(key=api_key, input=data, target=str(targetLanguage))).json()
	try:
		translatedText = tempDict['text'][0]
		return translatedText
	except KeyError:
		print 'Ignoring Debug Data'
		return 'There was a problem with the input'

# ====== TIMER FUNCTIONS ======

def printit():  
	threading.Timer(25.0, printit).start()

	print 'Keep Alive'

# ===============================

# queue = 13 #sets variable for anti-spam queue functionality
# Connect to server
print '\nConnecting to: ' + server + ' over port ' + str(port)
irc = socket.socket()
irc.connect((server, port))

# Send variables for connection to Twitch chat
irc.send('PASS ' + password + '\r\n')
irc.send('USER ' + nick + ' 0 * :' + botOwner + '\r\n')
irc.send('NICK ' + nick + '\r\n')
irc.send('JOIN ' + channel + '\r\n')

printit()

irc.send('PRIVMSG ' + channel + ' :/me has entered the channel.\r\n')

# translation_bot has entered the channel. Settings
# [ Target Language: jp | Filter Language: None | Broadcast: ON | !botcommands  | !about ]


# Main Program Loop
while True:
	
	ircdata = irc.recv(4096) # gets output from IRC server
	ircuser = ircdata.split(':')[1]
	ircuser = ircuser.split('!')[0] # determines the sender of the messages

	print 'DEBUG: ' + ircdata.strip(' \t\n\r')
	print '\n'
	user = getNick(ircdata).strip(' \t\n\r')
	print 'USER: ' + user
	print '\n'
	message = getMessage(ircdata).strip(' \t\n\r')
	print 'MESSAGE: ' + message
	print '\n'
	print '======================='


	# About
	if ircdata.find(':!about') != -1:
		irc.send('PRIVMSG ' + channel + ' :Salutations! I am a translation chat bot written by darkandark. I provide instant chat translation from any language to a desired target language. Type !botcommands to interact with me.\r\n')
	
	# Commands
	if ircdata.find(':!why') != -1:
		irc.send('PRIVMSG ' + channel + ' :Twitch Chat is a wonderful platform to connect gamers and build communities. Many streamers have a dual language audience. Having a translation bot in your channel may help viewers of different languages interact, increasing the quality of your chat for your viewers.\r\n')

	# Last
	if ircdata.find(':!last') != -1:
		irc.send('PRIVMSG ' + channel + ' :' + getLast() + '\r\n')

	# Last
	if ircdata.find(':!broadcast') != -1:
		tempMsg = message.strip('!broadcast')
		tempMsg = tempMsg.split()[0]
		if tempMsg.lower() == 'on':
			broadcast = 1;
		elif tempMsg.lower() == 'off':
			broadcast = 0;
		else:
			pass
			

	# Current Runes
	if ircdata.find(':!settings') != -1 or ircdata.find(':!setting') != -1:
		irc.send('PRIVMSG ' + channel + ' :' + getCurrent('runes') + '\r\n')

	# Current Mastery
	if ircdata.find(':!botcommands') != -1 or ircdata.find(':!botcommand') != -1:
		irc.send('PRIVMSG ' + channel + ' :' + getCurrent('masteries') + '\r\n')

	# Keep Alive
	if ircdata.find('PING') != -1:
		irc.send('PONG ' + ircdata.split()[1] + '\r\n')

	inputText = message
	if inputText == 'Not a message' or inputText == 'No message' or inputText == 'Index Error' or inputText[0] == '!':
		pass
	elif detectLanguage(str(inputText)) == str(filterLanguage) and broadcast == 1:
		print 'IS IT PICKING UP THAT IT IS ENGLIHS?'
		irc.send('PRIVMSG ' + channel + ' :/me : ' + user + ' said - [' + translateMessage(str(inputText)) + '] ' + '\r\n')
	else:
		print filterLanguage + ' not found.'
		pass
