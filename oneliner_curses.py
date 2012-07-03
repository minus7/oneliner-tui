#import Oneliner from oneliner
import logging
import urwid

class RollingListWalker(urwid.SimpleListWalker):
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

class OnelinerCurses(object):
	def __init__(self, baseUrl, historyLength=500):
		#self.oneliner = Oneliner(baseUrl, historyLength)
		
		self.log = logging.getLogger(self.__class__.__name__)
		
		palette = [
			('input', 'default', 'dark blue'),
		]
		
		self.chat = RollingListWalker()
		self.input = urwid.Edit("[not logged in] ", allow_tab=True, wrap='clip')
		def inputHappend(edit, new_text):
			if new_text == 'q':
				raise urwid.ExitMainLoop()
		urwid.connect_signal(self.input, 'change', inputHappend)
		
		frame = urwid.Frame(urwid.ListBox(self.chat), footer=urwid.AttrMap(self.input, 'input'))
		frame.set_focus('footer')
		def uhi(input):
			if input == 'enter':
				self.chat.append(urwid.Text(self.input.edit_text))
				self.input.set_edit_text("")
				self.chat.set_focus('end')
			if input == 'page up':
				self.chat.shift_focus(-5)
			if input == 'page down':
				self.chat.shift_focus(+5)
		self.loop = urwid.MainLoop(frame, palette, unhandled_input=uhi)
		
		self.log.info("Oneliner curses frontend initialized")
	
	def Run(self):
		self.loop.run()
	
	def CommandHistoryPrev(self):
		if self.commandIndex > 0:
			self.commandIndex -= 1
			self.inputWindow.clear()
			self.inputWindow.addstr(self.commandHistory[self.commandIndex])
			self.inputBuffer = self.commandHistory[self.commandIndex]
	
	def CommandHistoryNext(self):
		if self.commandIndex < len(self.commandHistory) - 1:
			self.commandIndex += 1
			self.inputWindow.clear()
			self.inputWindow.addstr(self.commandHistory[self.commandIndex])
			self.inputBuffer = self.commandHistory[self.commandIndex]
		elif self.commandIndex == len(self.commandHistory) - 1:
			self.commandIndex += 1
			self.inputWindow.clear()
			self.inputBuffer = ""
			
	
	def CommandEnter(self):
		if len(self.inputBuffer) == 0:
			return
		self.commandHistory.append(self.inputBuffer)
		# set index to the next free slot
		self.commandIndex = len(self.commandHistory)
		self.inputBuffer = ""
		self.inputWindow.clear()
	
	def __del__(self):
		self.log.info("Oneliner curses frontend destroyed")
