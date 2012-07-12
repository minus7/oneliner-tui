from twisted.internet import reactor
from twisted.internet.defer import Deferred
from twisted.internet.protocol import Protocol
from twisted.web.client import Agent, HTTPConnectionPool, getPage
from twisted.python.log import PythonLoggingObserver
from oneliner import Oneliner


class OnelinerTwisted(Oneliner):
	"""
	Subclass of Oneliner using twisted's async http client
	_Request/Monitor/GetNewLines return Deferreds
	"""
	
	def __init__(self, baseUrl, historyLength=50, reactor=None):
		# use the standard python logging module
		PythonLoggingObserver().start()
		
		self._Setup(baseUrl, historyLength)
		
		#if not reactor:
		#	from twisted.internet import reactor as reactor_
		#	reactor = reactor_
		#self.reactor = reactor
		#pool = HTTPConnectionPool(self.eventLoop.reactor, persistent=True)
		#pool.maxPersistentPerHost = 1
		#self.agent = Agent(self.eventLoop.reactor, pool=pool)
		
		self.log.info(u"OnelinerTwisted initialized")
	
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
