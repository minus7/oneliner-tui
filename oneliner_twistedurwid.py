import urwid
from twisted.internet import reactor
from twisted.internet.defer import Deferred
from twisted.internet.protocol import Protocol
from twisted.web.client import Agent, HTTPConnectionPool, getPage
from twisted.python.log import PythonLoggingObserver
from StringIO import StringIO
from oneliner import Oneliner


class OnelinerTwistedUrwid(Oneliner, urwid.ListWalker):
	"""
	async + ListWalker compatibility
	"""
	
	def __init__(self, baseUrl, historyLength=None, eventLoop=None):
		# use the standard python logging module
		PythonLoggingObserver().start()
		
		if not eventLoop:
			self.eventLoop = urwid.TwistedEventLoop()
		else:
			self.eventLoop = eventLoop
		pool = HTTPConnectionPool(self.eventLoop.reactor, persistent=True)
		pool.maxPersistentPerHost = 1
		self.agent = Agent(self.eventLoop.reactor, pool=pool)
		
		if historyLength:
			Oneliner.__init__(self, baseUrl, historyLength)
		else:
			Oneliner.__init__(self, baseUrl)
		
		# ListWalker focus
		self.focus = 'end'
	
	def _LogErrback(self, error):
		self.log.error(str(error))
		return error
		
	def _Request(self, url, method="GET", data=None):
		responseDeferred = getPage(self.baseUrl + url, method=method, postdata=data)
		responseDeferred.addErrback(self._LogErrback)
		return responseDeferred
	
	def Monitor(self):
		self.log.debug(u"Monitor called")
		deferredRequest = self._Request("/demovibes/ajax/monitor/{}/".format(self.nextEvent))
		def MonitorDone(data):
			if self.ParseMonitor(data):
				self.log.debug(u"New lines available, switching to GetNewLines")
				self.GetNewLines()
			else:
				self.log.debug(u"No new lines available, retrying")
				self.Monitor()
		deferredRequest.addCallback(MonitorDone)
	
	def GetNewLines(self):
		self.log.debug(u"GetNewLines called")
		deferredRequest = self._Request("/demovibes/xml/oneliner/")
		def GetNewLinesDone(data):
			if self.ParseOneliner(data):
				self.log.debug(u"New lines received, switching to monitor mode")
				self._modified()
			self.Monitor()
		deferredRequest.addCallback(GetNewLinesDone)
	
	# urwid ListWalker interface:
	
	def _GetAtPos(self, position):
		if position == 'end':
			position = len(self.history) - 1
		if position < 0 or position >= len(self.history):
			return (None, None)
		msg = self.history[position]
		text = u"[{}] {}: {}".format(msg.time, msg.author, msg.message)
		return (urwid.Text(text), position)
	
	def get_focus(self):
		return self._GetAtPos(self.focus)
	
	def set_focus(self, focus):
		self.focus = focus
		self._modified()
	
	def get_next(self, position):
		return self._GetAtPos(position + 1)
	
	def get_prev(self, position):
		return self._GetAtPos(position - 1)
