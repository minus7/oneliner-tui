import urwid
from oneliner import Oneliner


class OnelinerAsync(Oneliner):
	request = False
	response = None
	def _Request(self, url, method="GET"):
		"""
		returns a HTTPResponse object when ready,
		otherwise None (in async mode)
		"""
		# TODO: exception handling
		
		self.log.debug("async _Request: url={} request={} response={}".format(url, self.request, self.response))
		
		# send request
		if not self.request and not self.response:
			self.connection.request(method, self.basePath + url)
			self.request = True
			return None
		
		# handle response
		if self.request and not self.response:
			self.request = False
			self.response = self.connection.getresponse()
			return None
		
		if self.response and not self.request:
			response = self.response
			self.response = None
			return response
		
		raise Exception("This should not happen")


class OnelinerUrwid(OnelinerAsync, urwid.ListWalker):
	"""
	async + ListWalker compatibility
	"""
	def __init__(self, baseUrl, historyLength=None, eventLoop=None):
		if not eventLoop:
			eventLoop = urwid.SelectEventLoop()
		self.eventLoop = eventLoop
		
		if historyLength:
			OnelinerAsync.__init__(self, baseUrl, historyLength)
		else:
			OnelinerAsync.__init__(self, baseUrl)
		
		self.focus = 0
		
		# use fileno because it won't change and
		# connection.sock won't exist after getresonse()
		self.fd = -1
		self.step = 'monitor'
		self.Monitor()
		self.fd = self.connection.sock.fileno()
		self.eventLoop.watch_file(self.fd, self._DataAvailable)
		self.log.debug("OnelinerUrwid ready, watching fd={}".format(self.fd))
	
	def _DataAvailable(self):
		fd = -1
		if self.request:
			fd = self.connection.sock.fileno()
		elif self.response:
			fd = self.response.fileno()
		self.log.debug("connection fd={}".format(fd))
		if self.step == 'monitor':
			monitor = self.Monitor()
			if monitor is not None:
				if monitor is True:
					self.log.debug("New lines available, switching to getdata mode")
					self.step = 'getdata'
					self.GetNewLines()
				else:
					self.log.debug("No new lines available, retrying")
					self.Monitor()
			else:
				self.log.debug("Monitor request not done yet")
		elif self.step == 'getdata':
			lines = self.GetNewLines()
			if lines is not None:
				self.log.debug("New lines received, switching to monitor mode <-----------------------------------------------------------------------")
				self.step = 'monitor'
				self.Monitor()
				self._modified()
			else:
				self.log.debug("getdata request not done yet")
		self.log.debug("returning control to select")
	
	# urwid ListWalker interface:
	
	def _GetAtPos(self, position):
		if position < 0 or position >= len(self.history):
			return (None, None)
		msg = self.history[position]
		text = "[{}] {}: {}".format(msg.time, msg.author, msg.message)
		return (urwid.Text(text), position)
	
	def get_focus(self):
		return self._GetAtPos(self.focus)
	
	def set_focus(self, focus):
		if focus == 'end':
			if len(self.history) == 0: return
			focus = len(self.history) - 1
		self.focus = focus
		self._modified()
	
	def get_next(self, position):
		return self._GetAtPos(position + 1)
	
	def get_prev(self, position):
		return self._GetAtPos(position - 1)
