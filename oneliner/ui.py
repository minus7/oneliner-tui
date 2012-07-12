from async import OnelinerTwisted
import logging
import urwid

# TODO: song info
# TODO: rating
# TODO: bbcode
# TODO: colored nicks

class InputEdit(urwid.Edit):
	signals = ['change', 'send', 'historyprev', 'historynext']
	
	def keypress(self, size, key):
		if key == u'tab':
			# handle autocompletion
			# TODO: tab completion
			pass
		elif key == u'enter':
			# send stuff
			text = self.get_edit_text()
			if len(text) > 0:
				urwid.emit_signal(self, "send", self, text)
		elif key == u'up':
			# chat history
			urwid.emit_signal(self, "historyprev")
		elif key == u'down':
			# chat history
			urwid.emit_signal(self, "historynext")
		else:
			return urwid.Edit.keypress(self, size, key)
		
		return None
	
class OnelinerUrwid(OnelinerTwisted, urwid.ListWalker):
	"""
	ListWalker compatible Oneliner
	"""
	def __init__(self, base_url, history_length=2000, event_loop=None):
		
		if not event_loop:
			self.event_loop = urwid.TwistedEventLoop()
		else:
			self.event_loop = event_loop
		
		OnelinerTwisted.__init__(self, base_url, history_length=history_length, reactor=event_loop.reactor)
		
		# ListWalker focus
		self.focus = 'end'
	
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

class OnelinerUIUrwid(object):
	def __init__(self, base_url, history_length=500):
		self._log = logging.getLogger(self.__class__.__name__)
		
		self.commandIndex = 0
		self.commandHistory = [u""]
		
		self.event_loop = urwid.TwistedEventLoop()
		
		self.oneliner = OnelinerUrwid(base_url, history_length, self.event_loop)
		
		palette = [
			('input', 'default', 'dark blue'),
		]
		
		#self.chat = RollingListWalker()
		self.input = InputEdit(u"[not logged in] ", allow_tab=True, wrap='clip')
		urwid.connect_signal(self.input, 'change', self.command_change)
		urwid.connect_signal(self.input, 'send', self.command_enter)
		urwid.connect_signal(self.input, 'historyprev', self.command_history_prev)
		urwid.connect_signal(self.input, 'historynext', self.command_history_next)
		
		# contruct main layout (big output on the top,
		# one line input on the bottom) and set focus on input
		chat_listbox = urwid.ListBox(self.oneliner)
		chat_listbox.set_focus_valign('bottom')
		frame = urwid.Frame(chat_listbox, footer=urwid.AttrMap(self.input, 'input'))
		frame.set_focus('footer')
		
		def uhi(key):
			if key == u'page up':
				#self.chat.shift_focus(-5)
				# TODO
				pass
			elif key == u'page down':
				#self.chat.shift_focus(+5)
				# TODO
				pass
			elif key in (u'esc', u'ctrl d'):
				# TODO: other key to quit?
				raise urwid.ExitMainLoop()
			else:
				self._log.debug(u"unhandled input: {}".format(key))
		
		self.loop = urwid.MainLoop(frame, palette, unhandled_input=uhi, event_loop=self.event_loop)
		
		self._log.info(u"Oneliner curses frontend initialized")
		
		self.oneliner.monitor()
	
	def run(self):
		self.loop.run()
	
	def command_history_prev(self):
		if self.commandIndex > 0:
			self.commandIndex -= 1
			self.input.set_edit_text(self.commandHistory[self.commandIndex])
			self.input.set_edit_pos(len(self.commandHistory[self.commandIndex]))
	
	def command_history_next(self):
		if self.commandIndex < len(self.commandHistory) - 1:
			self.commandIndex += 1
			self.input.set_edit_text(self.commandHistory[self.commandIndex])
			self.input.set_edit_pos(len(self.commandHistory[self.commandIndex]))
	
	def command_change(self, edit, text):
		# remember changes the the current line
		# changes made to previous lines decay immediately
		if self.commandIndex == len(self.commandHistory) - 1:
			self.commandHistory[self.commandIndex] = text
	
	def command_enter(self, edit, text):
		if len(text) == 0:
			return
		if not self.oneliner.loggedIn:
			self.login_promt()
			return
		self.commandIndex = len(self.commandHistory)
		self.commandHistory[self.commandIndex - 1] = text
		self.commandHistory.append(u"")
		edit.set_edit_text(u"")
		self.oneliner.set_focus("end")
		# TODO: actually send stuff
	
	def login_promt():
		pass
	
	def __del__(self):
		self._log.info(u"Oneliner curses frontend destroyed")
