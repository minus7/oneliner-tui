from oneliner_twistedurwid import OnelinerTwistedUrwid
import logging
import urwid

# TODO: song info
# TODO: rating
# TODO: bbcode
# TODO: colored nicks

class RollingListWalker(urwid.SimpleListWalker):
	# TODO: make it roll
	def __init__(self, contents=None):
		if contents == None:
			 contents = []
		urwid.SimpleListWalker.__init__(self, contents)
	
	def set_focus(self, position):
		if position == 'end' and len(self.contents) > 0:
			position = len(self.contents) - 1
		urwid.SimpleListWalker.set_focus(self, position)
	
	def shift_focus(self, amount):
		position = self.get_focus()[1]
		if not position:
			return
		position += amount
		if position < 0:
			self.set_focus(0)
		elif position >= len(self.contents):
			self.set_focus(len(self.contents) - 1)
		else:
			self.set_focus(position)

class InputEdit(urwid.Edit):
	signals = ['change', 'send', 'historyprev', 'historynext']
	
	def keypress(self, size, key):
		if key == 'tab':
			# handle autocompletion
			# TODO: tab completion
			pass
		elif key == 'enter':
			# send stuff
			text = self.get_edit_text()
			if len(text) > 0:
				urwid.emit_signal(self, "send", self, text)
		elif key == 'up':
			# chat history
			urwid.emit_signal(self, "historyprev")
		elif key == 'down':
			# chat history
			urwid.emit_signal(self, "historynext")
		else:
			return urwid.Edit.keypress(self, size, key)
		
		return None

class OnelinerUICurses(object):
	def __init__(self, baseUrl, historyLength=500):
		self.log = logging.getLogger(self.__class__.__name__)
		
		self.commandIndex = 0
		self.commandHistory = [""]
		
		self.eventLoop = urwid.TwistedEventLoop()
		
		self.oneliner = OnelinerTwistedUrwid(baseUrl, historyLength, self.eventLoop)
		
		palette = [
			('input', 'default', 'dark blue'),
		]
		
		#self.chat = RollingListWalker()
		self.input = InputEdit("[not logged in] ", allow_tab=True, wrap='clip')
		urwid.connect_signal(self.input, 'change', self.CommandChange)
		urwid.connect_signal(self.input, 'send', self.CommandEnter)
		urwid.connect_signal(self.input, 'historyprev', self.CommandHistoryPrev)
		urwid.connect_signal(self.input, 'historynext', self.CommandHistoryNext)
		
		# contruct main layout (big output on the top,
		# one line input on the bottom) and set focus on input
		chatListBox = urwid.ListBox(self.oneliner)
		chatListBox.set_focus_valign('bottom')
		frame = urwid.Frame(chatListBox, footer=urwid.AttrMap(self.input, 'input'))
		frame.set_focus('footer')
		
		def uhi(key):
			if key == 'page up':
				#self.chat.shift_focus(-5)
				# TODO
				pass
			elif key == 'page down':
				#self.chat.shift_focus(+5)
				# TODO
				pass
			elif key in ('esc', 'ctrl d'):
				# TODO: other key to quit?
				raise urwid.ExitMainLoop()
			else:
				self.log.debug("unhandled input: {}".format(key))
		
		self.loop = urwid.MainLoop(frame, palette, unhandled_input=uhi, event_loop=self.eventLoop)
		
		self.log.info("Oneliner curses frontend initialized")
		
		self.oneliner.Monitor()
	
	def Run(self):
		self.loop.run()
	
	def CommandHistoryPrev(self):
		if self.commandIndex > 0:
			self.commandIndex -= 1
			self.input.set_edit_text(self.commandHistory[self.commandIndex])
			self.input.set_edit_pos(len(self.commandHistory[self.commandIndex]))
	
	def CommandHistoryNext(self):
		if self.commandIndex < len(self.commandHistory) - 1:
			self.commandIndex += 1
			self.input.set_edit_text(self.commandHistory[self.commandIndex])
			self.input.set_edit_pos(len(self.commandHistory[self.commandIndex]))
	
	def CommandChange(self, edit, text):
		# remember changes the the current line
		# changes made to previous lines decay immediately
		if self.commandIndex == len(self.commandHistory) - 1:
			self.commandHistory[self.commandIndex] = text
	
	def CommandEnter(self, edit, text):
		if len(text) == 0:
			return
		self.commandIndex = len(self.commandHistory)
		self.commandHistory[self.commandIndex - 1] = text
		self.commandHistory.append("")
		edit.set_edit_text("")
		self.oneliner.set_focus("end")
	
	def __del__(self):
		self.log.info("Oneliner curses frontend destroyed")
