from twisted.internet import reactor
from twisted.internet.defer import Deferred
from twisted.internet.protocol import Protocol
from twisted.web.client import Agent, HTTPConnectionPool, getPage, _makeGetterFactory, HTTPClientFactory
from twisted.python.log import PythonLoggingObserver
from urllib import urlencode
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
		
		if not reactor:
			from twisted.internet import reactor as reactor_
			reactor = reactor_
		self.reactor = reactor
		#pool = HTTPConnectionPool(self.event_loop.reactor, persistent=True)
		#pool.maxPersistentPerHost = 1
		#self.agent = Agent(self.event_loop.reactor, pool=pool)
		
		self._log.info(u"OnelinerTwisted initialized")
	
	def _log_errback(self, error):
		self._log.error(str(error))
		return error
		
	def _request(self, url, method="GET", data=None):
		deferred_response = getPage(self.base_url + url, method=method,
		                            postdata=data, cookies=self.cookies)
		deferred_response.addErrback(self._log_errback)
		return deferred_response
		
	def _request_cookies(self, url, method="GET", data=None):
		factory = _makeGetterFactory(self.base_url + url, HTTPClientFactory,
		                             method=method, postdata=data,
		                             cookies=self.cookies)
		factory.deferred.addErrback(self._log_errback)
		def cookie_magic(data):
			return (data, factory.cookies)
		factory.deferred.addCallback(cookie_magic)
		return factory.deferred
	
	def login(self, username, password):
		data = urlencode({'username': username, 'password': password})
		deferred_request = self._request_cookies("/account/signin/",
		                                         method="POST", data=data)
		if not deferred_request:
			return None
		
		def login_done((data, cookies)):
			# UTF-8 errors
			if "Please correct errors" in data:
				self._log.warning("Login failed")
				self._log.debug(data)
				self.logged_in = False
				return False
			
			if not "sessionid" in cookies:
				self.logged_in = False
				self._log.warning("Login failed")
				self._log.debug("Couldn't find cookie, dumping header")
				for name, value in cookies.iteritems():
					self._log.debug("header: '{}: {}'".format(name, value))
				return False
			
			self.cookies = cookies
			self._log.debug("Cookies: {}".format(cookies))
			
			self._log.info("Logged in as '{}'".format(username))
			self.logged_in = True
			return True
		
		deferred_request.addCallback(login_done)
		return deferred_request
	
	def send(self, message):
		if not self.logged_in:
			return False
		
		deferred_request = self._request("/demovibes/ajax/oneliner_submit/", method="POST",
		                                 data=urlencode({'Line': message}))
		if not deferred_request:
			return None
		
		def send_done(data):
			self._log.debug(data)
		deferred_request.addCallback(send_done)
		return deferred_request
	
	def monitor(self):
		self._log.debug(u"monitor called")
		deferred_request = self._request("/demovibes/ajax/monitor/{}/".format(self.next_event))
		def monitor_done(data):
			if self.parse_monitor(data):
				self._log.debug(u"New lines available, switching to get_new_lines")
				# ugly hack to get new lines more reliably
				# events seem to fire already if data isn't available yet
				self.reactor.callLater(0.5, self.get_new_lines)
			else:
				self._log.debug(u"No new lines available, retrying")
				self.monitor()
		deferred_request.addCallback(monitor_done)
		return deferred_request
	
	def get_new_lines(self):
		self._log.debug(u"get_new_lines called")
		deferred_request = self._request("/demovibes/xml/oneliner/")
		def get_new_lines_done(data):
			if self.parse_oneliner(data):
				self._log.debug(u"New lines received, switching to monitor mode")
				self._modified()
			self.monitor()
		deferred_request.addCallback(get_new_lines_done)
		return deferred_request
