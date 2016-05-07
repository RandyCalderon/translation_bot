# Twitch Translation Chat Bot
# A chat bot written in Python that automatically will translate your Twitch chat language for your foriegn viewers.
# 2016 - Benjamin Chu - v0.1

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
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

# =============================================
# FEATURE LIST - Add
# - Ability for users to change target language in chat
# - Static settings file
# - Whisper mode
# # =============================================
# BUG LIST
# - Quick successive message cause index error. Need to find a way to parse out the ircdata properly

class APIROUTES:
	yandex_detect = 'https://translate.yandex.net/api/v1.5/tr.json/detect?key={key}&text={input}'
	yandex_translate = 'https://translate.yandex.net/api/v1.5/tr.json/translate?key={key}&text={input}&lang={target}'
	google_detect = 'https://www.googleapis.com/language/translate/v2/detect?key={key}&q={input}'
	google_translate = 'https://www.googleapis.com/language/translate/v2?key={key}&q={input}&source={source}&target={target}'
	#google_auto_translate = 'https://www.googleapis.com/language/translate/v2?key={key}&q={input}&target={target}'

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
channel = '#darkandark'
# channel = '#' + ConfigSectionMap('settings')['channel']
server = ConfigSectionMap('settings')['server']
port = int(ConfigSectionMap('settings')['port'])
password = ConfigSectionMap('settings')['oauth']
yandex_api_key = ConfigSectionMap('settings')['yandexapi']
google_api_key = ConfigSectionMap('settings')['googleapi']

# Translation Bot Default Settings
targetLanguage = 'ja' # translating TO
sourceLanguage = 'en' # translating FROM
duplex = 0 # 1 for ON | 0 for OFF
broadcast = 1 # 1 for ON | 0 for OFF
translateAPI = 'google' # google | yandex

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
			return 'Message Error'
		except:
			return 'Message Error'
	else:
		return 'Message Error'

def detectLanguage(data):
	if translateAPI == 'yandex':
		# Get json data put into a dictionary
		tempDict = requests.get(APIROUTES.yandex_detect.format(key=yandex_api_key, input=data)).json()
		try:
			language = tempDict['lang']
			return str(language)
		except KeyError:
			print 'Problem with detection.'
			return 'Could not detect language.'
	elif translateAPI == 'google':
		tempDict = requests.get(APIROUTES.google_detect.format(key=google_api_key, input=data)).json()
		try:
			language = tempDict['data']['detections'][0][0]['language']
			#isReliable = tempDict['data']['detections'][0][0]['isReliable']
			#confidence = tempDict['data']['detections'][0][0]['confidence']
			return str(language)
		except KeyError:
			print 'Problem with detection.'
			return 'Could not detect language.'
	# Defaults to google's API
	else:
		tempDict = requests.get(APIROUTES.google_detect.format(key=google_api_key, input=data)).json()
		try:
			language = tempDict['data']['detections'][0][0]['language']
			#isReliable = tempDict['data']['detections'][0][0]['isReliable']
			#confidence = tempDict['data']['detections'][0][0]['confidence']
			return str(language)
		except KeyError:
			print 'Problem with detection.'
			return 'Could not detect language.'

def translateMessage(data, sourceLanguage, targetLanguage):
	print 'Translating: ' + data
	if translateAPI == 'yandex':
		tempDict = requests.get(APIROUTES.yandex_translate.format(key=yandex_api_key, input=data, target=str(targetLanguage))).json()
		try:
			translatedText = tempDict['text'][0]
			print 'Result: ' + translatedText
			return translatedText
		except KeyError:
			print 'Ignoring Debug Data'
			return 'Input Error'
	elif translateAPI == 'google':
		tempDict = requests.get(APIROUTES.google_translate.format(key=google_api_key, input=data, source=str(sourceLanguage), target=str(targetLanguage))).json()
		try:
			translatedText = tempDict['data']['translations'][0]['translatedText']
			print 'Result: ' + translatedText
			return translatedText
		except KeyError:
			print 'Ignoring Debug Data'
			return 'Input Error'
	# Defaults to Google API
	else:
		tempDict = requests.get(APIROUTES.google_translate.format(key=google_api_key, input=data, source=str(sourceLanguage), target=str(targetLanguage))).json()
		try:
			translatedText = tempDict['data']['translations'][0]['translatedText']
			print 'Result: ' + translatedText
			return translatedText
		except KeyError:
			print 'Ignoring Debug Data'
			return 'Input Error'


# ====== TIMER FUNCTIONS ======

def keepAlive():  
	threading.Timer(60.0, keepAlive).start()

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

keepAlive()
currentSettings = 'Current Settings: [' + sourceLanguage.upper() + '<->' + targetLanguage.upper()\
			+'] [Using ' + translateAPI.title() + ' Translate API] [Broadcast ' + str(broadcast)\
			+'] [Duplex ' + str(duplex) + ']'   
irc.send('PRIVMSG ' + channel + ' :/me has entered the channel. ' + currentSettings + ' \r\n')

# Main Program Loop
while True:
	
	ircdata = irc.recv(4096) # gets output from IRC server
	ircuser = ircdata.split(':')[1]
	ircuser = ircuser.split('!')[0] # determines the sender of the messages

	print 'DEBUG:\n' + ircdata.strip(' \t\n\r') + '\n'
	user = getNick(ircdata).strip(' \t\n\r')
	print 'USER:\n' + user + '\n'
	message = getMessage(ircdata).strip(' \t\n\r')
	print 'MESSAGE:\n' + message
	print '======================='

	# About
	if ircdata.find(':!about') != -1:
		irc.send('PRIVMSG ' + channel + ' :Salutations! I am a translation chat bot written by darkandark. I provide instant chat translation from any language to a desired target language. Type !botcommands to interact with me.\r\n')
	
	# Commands
	if ircdata.find(':!why') != -1:
		irc.send('PRIVMSG ' + channel + ' :Twitch Chat is a wonderful platform to connect gamers and build communities. Many streamers have a dual language audience. Having a translation bot in your channel may help viewers of different languages interact, increasing the quality of your chat for your viewers.\r\n')

	# !broadcast
	if ircdata.find(':!broadcast') != -1:
		tempMsg = message.strip('!broadcast')
		try:
			tempMsg = tempMsg.split()[0]
			if tempMsg.lower() == 'on' or tempMsg == '1':
				irc.send('PRIVMSG ' + channel + ' :Broadcast set to ON.\r\n')	
				broadcast = 1;
			elif tempMsg.lower() == 'off' or tempMsg == '0':
				irc.send('PRIVMSG ' + channel + ' :Broadcast set to OFF.\r\n')
				broadcast = 0;
			else:
				irc.send('PRIVMSG ' + channel + ' :Broadcast not set!\r\n')
				print 'Broadcast Not Set'
		except IndexError:
			print 'Broadcast Not Set'

	# !duplex | Bi-Directional Translation
	if ircdata.find(':!duplex') != -1:
		tempMsg = message.strip('!duplex')
		try:
			tempMsg = tempMsg.split()[0]
			if tempMsg.lower() == 'on' or tempMsg == '1':
				irc.send('PRIVMSG ' + channel + ' :Duplex set to ON.\r\n')
				duplex = 1;
			elif tempMsg.lower() == 'off' or tempMsg == '0':
				irc.send('PRIVMSG ' + channel + ' :Duplex set to OFF.\r\n')
				duplex = 0;
			else:
				irc.send('PRIVMSG ' + channel + ' :Duplex not set!\r\n')
				print 'Duplex Not Set'
		except IndexError:
			print 'Duplex Not Set'
			
	# Current Runes
	if ircdata.find(':!settings') != -1 or ircdata.find(':!setting') != -1:
		print 'duplex ' + str(duplex)
		print 'sourceLang ' + str(sourceLanguage)
		print 'targetLang ' + str(targetLanguage)
		print 'Broadcast ' + str(broadcast)

		currentSettings = 'Current Settings: [' + sourceLanguage.upper() + '<->' + targetLanguage.upper()\
			+'] [Using ' + translateAPI.title() + ' Translate API] [Broadcast ' + str(broadcast)\
			+'] [Duplex ' + str(duplex) + ']'   
		irc.send('PRIVMSG ' + channel + ' :' + currentSettings + '\r\n')

	# Keep Alive
	if ircdata.find('PING') != -1:
		irc.send('PONG ' + ircdata.split()[1] + '\r\n')

	inputText = message
	if inputText == 'Message Error' or inputText[0] == '!':
		pass
	elif detectLanguage(str(inputText)) == str(sourceLanguage) and broadcast == 1:
		irc.send('PRIVMSG ' + channel + ' :/me : ' + user + ' > [' + translateMessage(str(inputText), sourceLanguage, targetLanguage) + '] ' + '\r\n')
	elif duplex == 1:
		irc.send('PRIVMSG ' + channel + ' :/me : ' + user + ' > [' + translateMessage(str(inputText), targetLanguage, sourceLanguage) + '] ' + '\r\n')
	else:
		print 'Broadcast Disabled / Bi-Direction Disabled / Source Language Not Found'
		pass
