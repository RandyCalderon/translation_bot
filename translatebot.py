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
	lang_detect = 'https://translate.yandex.net/api/v1.5/tr.json/detect?key={key}'
	translate = 'https://translate.yandex.net/api/v1.5/tr.json/translate?key={key}&text={input}&lang={direction}'

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

def translateMessage(data):
	tempDict = requests.get(APIROUTES.translate.format(key=api_key, input=inputText, direction='zh')).json()
	try:
		translatedText = tempDict['text'][0]
		return translatedText
	except KeyError:
		print 'Ignoring Debug Data'
		return 'There was a problem with the input'

# ====== TIMER FUNCTIONS ======

def printit():  
	threading.Timer(60.0, printit).start()
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

# Main Program Loop
while True:

	ircdata = irc.recv(1024) # gets output from IRC server
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

	inputText = message
	if inputText == 'Not a message' or inputText == 'No message' or inputText == 'Index Error':
		pass
	else:
		irc.send('PRIVMSG ' + channel + ' :/me : ' + user + ' said - [' + translateMessage(str(inputText)) + '] ' + '\r\n')

	# About
	if ircdata.find(':!about') != -1:
		irc.send('PRIVMSG ' + channel + ' :' + about(getNick(ircdata)) + '\r\n')

	# Commands
	if ircdata.find(':!commands') != -1:
		irc.send('PRIVMSG ' + channel + ' :' + getCommands() + '\r\n')

	# Last
	if ircdata.find(':!last') != -1:
		irc.send('PRIVMSG ' + channel + ' :' + getLast() + '\r\n')

	# Current Runes
	if ircdata.find(':!runes') != -1 or ircdata.find(':!rune') != -1:
		irc.send('PRIVMSG ' + channel + ' :' + getCurrent('runes') + '\r\n')

	# Current Mastery
	if ircdata.find(':!mastery') != -1 or ircdata.find(':!masteries') != -1:
		irc.send('PRIVMSG ' + channel + ' :' + getCurrent('masteries') + '\r\n')

	# Basic Summoner Data
	if ircdata.find(':!summoner') != -1:
		irc.send('PRIVMSG ' + channel + ' :' + getSummonerInfo() + '\r\n')

	# Keep Alive
	if ircdata.find('PING') != -1:
		irc.send('PONG ' + ircdata.split()[1] + '\r\n')


