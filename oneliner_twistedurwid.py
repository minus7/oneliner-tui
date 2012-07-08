import urwid
from twisted.internet import reactor
from twisted.internet.defer import Deferred
from twisted.internet.protocol import Protocol
from twisted.web.client import Agent, HTTPConnectionPool, FileBodyProducer, ResponseDone
from twisted.python.log import PythonLoggingObserver
from StringIO import StringIO
from oneliner import Oneliner


class DataWaiter(Protocol):
	def __init__(self, finished):
		self.finished = finished
		self.data = ''

	def dataReceived(self, bytes):
		self.data += bytes

	def connectionLost(self, reason):
		if isinstance(reason, ResponseDone):
			self.finished.callback(self.data)
			return self.data
		else:
			raise reason

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
		if data:
			data = FileBodyProducer(StringIO(data))
		request = self.agent.request(method, self.baseUrl + url, bodyProducer=data)
		request.addErrback(self._LogErrback)
		def RequestCallback(response):
			finished = Deferred()
			response.deliverBody(DataWaiter(finished))
			finished.addErrback(self._LogErrback)
			return finished
		request.addCallback(RequestCallback)
		return request
	
	def Monitor(self):
		self.log.debug("Monitor called")
		deferredRequest = self._Request("/demovibes/ajax/monitor/{}/".format(self.nextEvent))
		def MonitorDone(dataWaiter):
			if self.ParseMonitor(dataWaiter.data):
				self.log.debug("New lines available, switching to GetNewLines")
				self.GetNewLines()
			else:
				self.log.debug("No new lines available, retrying")
				self.Monitor()
		deferredRequest.addCallback(MonitorDone)
	
	def GetNewLines(self):
		self.log.debug("GetNewLines called")
		deferredRequest = self._Request("/demovibes/xml/oneliner/")
		def GetNewLinesDone(dataWaiter):
			if self.ParseOneliner(dataWaiter.data):
				self.log.debug("New lines received, switching to monitor mode")
				self._modified()
			self.Monitor()
		deferredRequest.addCallback(MonitorDone)
	
	# urwid ListWalker interface:
	
	def _GetAtPos(self, position):
		if position == 'end':
			position = len(self.history) - 1
		if position < 0 or position >= len(self.history):
			return (None, None)
		msg = self.history[position]
		text = "[{}] {}: {}".format(msg.time, msg.author, msg.message)
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
