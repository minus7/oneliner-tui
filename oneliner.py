#import http.client
#from cookielib import MozillaCookieJar
import re
import datetime
from xml.etree import ElementTree
import logging

#~ import sys
#~ reload(sys)
#~ sys.setdefaultencoding('utf8')

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
		host: host of the demovibes installation
		historyLength: how many onelines to keep in the buffer
		baseUrl: path to the demovibes installation
		"""
		self.baseUrl = baseUrl
		#self.connection = http.client.HTTPConnection(host)
		self.history = []
		self.historyLength = historyLength
		self.nextEvent = 0
		
		self.log = logging.getLogger(self.__class__.__name__)
		self.log.info(u"Oneliner initialized")
	
	def Login(self, username, password):
		raise NotImplementedError(u"Login not implemented")
	
	def Send(self, message):
		if not self.loggedIn:
			self.log.warning(u"Tried to send message without being logged in")
		raise NotImplementedError(u"Sending not implemented")
	
	def _Request(self, url, method="GET"):
		"""
		returns a HTTPResponse object when ready,
		otherwise None (in async mode)
		"""
		# TODO: exception handling
		self.connection.request(method, self.baseUrl + url)
		return self.connection.getresponse()
	
	def Monitor(self):
		"""
		returns True if new lines are available
		returns None if the request failed
		"""
		response = self._Request("/demovibes/ajax/monitor/{}/".format(self.nextEvent))
		if not response:
			return None
		
		data = response.read()
		return self.ParseMonitor(data)
	
	def ParseMonitor(self, data):
		lines = data.splitlines()
		
		# find next event ID
		oldEvent = self.nextEvent
		# future remark: ord("!") required in python 3
		if lines[-1][0] == "!":
			self.nextEvent = int(lines[-1][1:])
			self.log.debug(u"Next event ID: {}".format(self.nextEvent))
		else:
			self.log.warning(u"Couldn't find the next event ID in message")
			self.log.debug(u"Event data: {}".format(repr(data)))
		
		if u"oneliner" in lines or oldEvent == 0:
			return True
		else:
			self.log.debug(u"No oneliner event, retrying")
			return False
	
	def ParseOneliner(self, data):
		"""
		parse oneliner XML
		"""
		
		try:
			oneliner = ElementTree.fromstring(data)
		except ElementTree.ParseError as e:
			self.log.error(u"Oneliner XML parsing failed: {}".format(str(e)))
			return []
		
		self.log.debug(u"Oneliner data: {}...".format(repr(data[:20])))
		
		newLines = []
		for msg in oneliner.iterfind('entry'):
			# parses "Sun, 12 Feb 2012 01:00:48 +0100" (date offset is cut off for now)
			# TODO: timezone offset parsing?
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
		self.log.debug(u"Added {} new lines".format(len(newLines)))
		
		return newLines
	
	def GetNewLines(self):
		"""
		receives new oneliner data and returns new lines only
		returns None if the request failed
		"""
		response = self._Request("/demovibes/xml/oneliner/")
		if not response:
			return None
		
		return self.ParseOneliner(response.read())
	
	def GetLines(self, lines=10, block=False):
		"""
		returns the last `lines` lines (default: 10)
		waits for the requested amount of lines
		to be buffered if `block` is True
		"""
		while block and len(self.history) < lines:
			self.GetNewLines()
		
		return self.history[-lines:]

