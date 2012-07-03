#import Oneliner from oneliner
import logging
import curses

class OnelinerCurses(object):
	def __init__(self, baseUrl, historyLength=500):
		#self.oneliner = Oneliner(baseUrl, historyLength)
		
		self.commandHistory = []
		self.commandIndex = 0
		
		self.log = logging.getLogger(self.__class__.__name__)
		
		self.InitCurses()
		
		self.log.info("Oneliner curses frontend initialized")
	
	def InitCurses(self):
		# initialize standard screen
		self.screen = curses.initscr()
		# don't echo key input
		curses.noecho()
		# turn off buffered mode (so the program
		# receives key presses without waiting for enter)
		curses.cbreak()
		# enable handling of special keys (like arrow keys)
		# in curses
		self.screen.keypad(1)
		# enable colors
		curses.start_color()
		
		# create the buffer window
		self.bufferWindow = curses.newwin(0, 0, 0, 0)
		self.inputWindow = curses.newwin(0, 0, 0, 0)
	
	def TerminateCurses(self):
		#re-enable buffered input mode
		curses.nocbreak()
		# disable special key parsing (why?)
		self.screen.keypad(0)
		# re-enable echoing
		curses.echo()
		# restore original operating mode
		curses.endwin()
	
	def Resize(self):
		(y,x) = self.screen.getmaxyx()
		self.bufferWindow.move(0, 0)
		self.bufferWindow.resize(y - 1, x)
		self.inputWindow.move(y - 1, 0)
		self.inputWindow.resize(1, x)
		self.screen.refresh()
	
	def Run(self):
		#curses.wrapper(self.RunImpl)
		while True:
			try:
				# process input
				ch = self.inputWindow.getch()
				if ch == curses.KEY_RESIZE:
					self.Resize()
				elif ch == curses.KEY_UP:
					self.CommandHistoryPrev()
				elif ch == curses.KEY_DOWN:
					self.CommandHistoryNext()
				elif curses.ASCII.isascii(ch):
					self.inputWindow.addch(ch)
					self.inputBuffer += ord(ch)
			except Exception:
				self.TerminateCurses()
				raise
	
	def CommandHistoryPrev(self):
		if self.commandIndex > 0:
			self.commandIndex -= 1
			self.inputWindow.clear()
			self.inputWindow.addstr(self.commandHistory[self.commandIndex])
	
	def CommandHistoryNext(self):
		if self.commandIndex < len(self.commandHistory):
			self.commandIndex += 1
			self.inputWindow.clear()
			self.inputWindow.addstr(self.commandHistory[self.commandIndex])
	
	def RunImpl(self, key):
		pass
	
	def __del__(self):
		self.TerminateCurses()
		self.log.info("Oneliner curses frontend destroyed")