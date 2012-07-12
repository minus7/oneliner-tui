from twisted.internet import reactor
from twisted.internet.defer import Deferred
from twisted.internet.protocol import Protocol
from twisted.web.client import Agent, HTTPConnectionPool, getPage
from twisted.python.log import PythonLoggingObserver
from oneliner import Oneliner


class OnelinerTwisted(Oneliner):
	"""
	Subclass of Oneliner using twisted's async http client
	_request/monitor/get_new_lines return Deferreds
	"""
	
	def __init__(self, base_url, history_length=50, reactor=None):
		# use the standard python logging module
		PythonLoggingObserver().start()
		
		self._setup(base_url, history_length)
		
		#if not reactor:
		#	from twisted.internet import reactor as reactor_
		#	reactor = reactor_
		#self.reactor = reactor
		#pool = HTTPConnectionPool(self.event_loop.reactor, persistent=True)
		#pool.maxPersistentPerHost = 1
		#self.agent = Agent(self.event_loop.reactor, pool=pool)
		
		self._log.info(u"OnelinerTwisted initialized")
	
	def _log_errback(self, error):
		self._log.error(str(error))
		return error
		
	def _request(self, url, method="GET", data=None):
		deferred_response = getPage(self.base_url + url, method=method, postdata=data)
		deferred_response.addErrback(self._log_errback)
		return deferred_response
	
	def monitor(self):
		self._log.debug(u"monitor called")
		deferred_request = self._request("/demovibes/ajax/monitor/{}/".format(self.next_event))
		def monitor_done(data):
			if self.parse_monitor(data):
				self._log.debug(u"New lines available, switching to get_new_lines")
				self.get_new_lines()
			else:
				self._log.debug(u"No new lines available, retrying")
				self.monitor()
		deferred_request.addCallback(monitor_done)
	
	def get_new_lines(self):
		self._log.debug(u"get_new_lines called")
		deferred_request = self._request("/demovibes/xml/oneliner/")
		def get_new_lines_done(data):
			if self.parse_oneliner(data):
				self._log.debug(u"New lines received, switching to monitor mode")
				self._modified()
			self.monitor()
		deferred_request.addCallback(get_new_lines_done)
