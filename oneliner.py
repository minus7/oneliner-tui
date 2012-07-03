import urllib2
#from cookielib import MozillaCookieJar
import re
import datetime
from xml.etree import ElementTree
import logging

import sys
reload(sys)
sys.setdefaultencoding('utf8')

#cj = MozillaCookieJar("mycookies.txt")
#cj.load()
#opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))

class OnelinerMessage(object):
	def __init__(self, author, message, time):
		self.author = author
		self.message = message
		self.time = time

class Oneliner(object):
	def __init__(self, baseUrl, historyLength=50):
		"""
		baseUrl: base url of the demovibes installation
		historyLength: how many onelines to keep in the buffer (default: 50)
		"""
		self.baseUrl = baseUrl
		self.opener = urllib2.build_opener()
		self.history = []
		self.historyLength = historyLength
		self.nextEvent = 0
		self.log = logging.getLogger(self.__class__.__name__)
		self.log.info("Oneliner initialized")
	
	def Login(self, username, password):
		raise Exception("not implemented")
	
	def Send(self, message):
		if not self.loggedIn:
			self.log.warning("Tried to send message without being logged in")
		raise Exception("not implemented")
	
	def GetMoreLines(self):
		"""
		waits for more lines and returns newly received ones
		"""
		req = self.opener.open("{}/demovibes/ajax/monitor/{}/".format(self.baseUrl, self.nextEvent))
		data = req.read()
		lines = data.splitlines()
		
		# find next event ID
		oldEvent = self.nextEvent
		if lines[-1][0] == "!":
			self.nextEvent = int(lines[-1][1:])
			self.log.debug("Next event ID: {}".format(self.nextEvent))
		else:
			self.log.warning("Couldn't find the next event ID in message")
			self.log.debug("Event data: " + repr(data))
		
		if "oneliner" in lines or oldEvent == 0:
			data = self.opener.open("{}/demovibes/xml/oneliner/".format(self.baseUrl)).read()
			try:
				oneliner = ElementTree.fromstring(data)
			except ElementTree.ParseError as e:
				self.log.error("Oneliner XML parsing failed: " + str(e))
				return []
			
			self.log.debug("Oneliner data: " + repr(data))
			
			newLines = []
			for msg in oneliner.iterfind('entry'):
				# parses "Sun, 12 Feb 2012 01:00:48 +0100" (date offset is cut off for now)
				msgTime = datetime.datetime.strptime(msg.get('time')[:-6], "%a, %d %b %Y %H:%M:%S")
				msgAuthor = msg.find('author').text
				msgText = msg.find('message').text
				if len(self.history) > 0 and \
					self.history[-1].time == msgTime and \
					self.history[-1].author == msgAuthor and \
					self.history[-1].message == msgText:
					break
				newLines.append(OnelinerMessage(msgAuthor, msgText, msgTime))
			
			# get the new stuff into the right order
			newLines.reverse()
			# append new stuff, removing old lines if necesssary
			self.history = self.history[-self.historyLength+len(newLines):] + newLines
			self.log.debug("Added {} new lines".format(len(newLines)))
			
			return newLines
		else:
			self.log.debug("No oneliner event, retrying")
			return []
	
	def GetLines(self, lines=10, block=True):
		"""
		returns the last `lines` lines (default: 10)
		waits for the requested amount of lines
		to be buffered if `block` is True
		"""
		while block and len(history) < lines:
			self.GetMoreLines()
		
		return history[-lines:]


if __name__ == "__main__":
	log = logging.getLogger("Oneliner")
	log.setLevel(logging.DEBUG)
	logFormatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
	#logHandler = logging.FileHandler("test.log")
	logHandler = logging.StreamHandler()
	logHandler.setLevel(logging.WARNING)
	#logHandler.setLevel(logging.DEBUG)
	logHandler.setFormatter(logFormatter)
	log.addHandler(logHandler)

	o = Oneliner("http://www.scenemusic.net/")

	while True:
		lines = o.GetMoreLines()
		
		for line in lines:
			print("[{}] {}: {}".format(line.time, line.author, line.message))
