from httplib import HTTPConnection
import re
import datetime
from xml.etree import ElementTree
import logging
from urlparse import urlparse

class OnelinerMessage(object):
	def __init__(self, author, message, time):
		self.author = author
		self.message = message
		self.time = time

class Oneliner(object):
	def __init__(self, base_url, history_length=50):
		self._setup(base_url, history_length)
		
		url_info = urlparse(base_url)
		self.base_path = url_info.path
		self.connection = HTTPConnection(url_info.netloc)
		
		self._log.info(u"Oneliner initialized")
	
	def _setup(self, base_url, history_length):
		"""
		history_length: how many onelines to keep in the buffer
		base_url: url to the base of the demovibes installation
		"""
		self._log = logging.getLogger(self.__class__.__name__)
		self.base_url = base_url
		self.history = []
		self.history_length = history_length
		self.next_event = 0
		self.loggedIn = False
	
	def Login(self, username, password):
		raise NotImplementedError(u"Login not implemented")
	
	def Send(self, message):
		raise NotImplementedError(u"Sending not implemented")
	
	def _request(self, url, method="GET"):
		"""
		returns a HTTPResponse object when ready,
		otherwise None (in async mode)
		"""
		# TODO: exception handling
		self.connection.request(method, self.base_path + url)
		return self.connection.getresponse()
	
	def monitor(self):
		"""
		returns True if new lines are available
		returns None if the request failed
		"""
		response = self._request("/demovibes/ajax/monitor/{}/".format(self.next_event))
		if not response:
			return None
		
		data = response.read()
		return self.parse_monitor(data)
	
	def parse_monitor(self, data):
		lines = data.splitlines()
		
		# find next event ID
		old_event = self.next_event
		# future remark: ord("!") required in python 3
		if lines[-1][0] == "!":
			self.next_event = int(lines[-1][1:])
			self._log.debug(u"Next event ID: {}".format(self.next_event))
		else:
			self._log.warning(u"Couldn't find the next event ID in message")
			self._log.debug(u"Event data: {}".format(repr(data)))
		
		if u"oneliner" in lines or old_event == 0:
			return True
		else:
			self._log.debug(u"No oneliner event, retrying")
			return False
	
	def parse_oneliner(self, data):
		"""
		parse oneliner XML
		"""
		
		try:
			oneliner = ElementTree.fromstring(data)
		except ElementTree.ParseError as e:
			self._log.error(u"Oneliner XML parsing failed: {}".format(str(e)))
			return []
		
		self._log.debug(u"Oneliner data: {}...".format(repr(data[:20])))
		
		new_lines = []
		for msg in oneliner.iterfind('entry'):
			# parses "Sun, 12 Feb 2012 01:00:48 +0100" (date offset is cut off for now)
			# TODO: timezone offset parsing?
			msg_time = datetime.datetime.strptime(msg.get('time')[:-6], "%a, %d %b %Y %H:%M:%S")
			msg_author = msg.find('author').text
			msg_text = msg.find('message').text
			if len(self.history) > 0 and \
				self.history[-1].time == msg_time and \
				self.history[-1].author == msg_author and \
				self.history[-1].message == msg_text:
				break
			new_lines.append(OnelinerMessage(msg_author, msg_text, msg_time))
		
		# get the new stuff into the right order
		new_lines.reverse()
		# append new stuff, removing old lines if necesssary
		self.history = self.history[-self.history_length+len(new_lines):] + new_lines
		self._log.debug(u"Added {} new lines".format(len(new_lines)))
		
		return new_lines
	
	def get_new_lines(self):
		"""
		receives new oneliner data and returns new lines only
		returns None if the request failed
		"""
		response = self._request("/demovibes/xml/oneliner/")
		if not response:
			return None
		
		return self.parse_oneliner(response.read())
	
	def get_lines(self, lines=10, block=False):
		"""
		returns the last `lines` lines (default: 10)
		waits for the requested amount of lines
		to be buffered if `block` is True
		"""
		while block and len(self.history) < lines:
			self.get_new_lines()
		
		return self.history[-lines:]

