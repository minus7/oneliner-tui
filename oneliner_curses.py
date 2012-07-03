#import Oneliner from oneliner
import logging
import curses, curses.wrapper

class OnelinerCurses(object):
	def __init__(self, baseUrl, historyLength=500):
		#self.oneliner = Oneliner(baseUrl, historyLength)
		
		self.commandHistory = []
		self.commandIndex = 0
		self.inputBuffer = ""
		
		self.log = logging.getLogger(self.__class__.__name__)
		
		self.InitCurses()
		
		self.log.info("Oneliner curses frontend initialized")
	
	def InitCurses(self):
		try:
			# initialize standard screen
			self.screen = curses.initscr()
			# don't echo key input
			curses.noecho()
			# turn off buffered mode (so the program
			# receives key presses without waiting for enter)
			curses.cbreak()
			# enable handling of special keys (like arrow keys)
			# in curses
			#self.screen.keypad(1)
			# enable colors
			curses.start_color()
			
			curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLUE)
			self.inputColor = curses.color_pair(1)
		
			# create the buffer window
			(y,x) = self.screen.getmaxyx()
			self.bufferWindow = curses.newwin(y - 1, x, 0, 0)
			self.inputWindow = curses.newwin(1, x, y - 1, 0)
			self.inputWindow.bkgd(" ", self.inputColor)
			self.inputWindow.keypad(1)
		except:
			self.TerminateCurses()
			raise
	
	def TerminateCurses(self):
		#re-enable buffered input mode
		curses.nocbreak()
		# disable special key parsing (why?)
		#self.screen.keypad(0)
		# re-enable echoing
		curses.echo()
		# restore original operating mode
		curses.endwin()
	
	def Resize(self):
		(y,x) = self.screen.getmaxyx()
		self.bufferWindow.mvwin(0, 0)
		self.bufferWindow.resize(y - 1, x)
		self.bufferWindow.noutrefresh()
		self.inputWindow.mvwin(y - 1, 0)
		self.inputWindow.resize(1, x)
		self.inputWindow.noutrefresh()
		self.screen.doupdate()
	
	def Run(self):
		#curses.wrapper(self.RunImpl)
		while True:
			try:
				# process input
				ch = self.inputWindow.getch()
				self.bufferWindow.addstr(str(ch)+"\n")
				self.bufferWindow.refresh()
				if ch == ord('q'):
					return
				elif ch == curses.KEY_RESIZE:
					self.Resize()
				elif ch == curses.KEY_UP:
					self.CommandHistoryPrev()
				elif ch == curses.KEY_DOWN:
					self.CommandHistoryNext()
				elif ch == ord("\n"): # enter
					if len(self.inputBuffer) > 0:
						self.bufferWindow.addstr(self.inputBuffer + "\n")
						self.bufferWindow.refresh()
					self.CommandEnter()
				elif ch == curses.KEY_BACKSPACE or ch == 127: # backspace
					self.inputBuffer = self.inputBuffer[:-1]
					self.inputWindow.clear()
					self.inputWindow.addstr(self.inputBuffer)
				elif ch >= 32 and ch <= 255:
					self.inputWindow.addch(ch, self.inputColor)
					self.inputBuffer += chr(ch)
			except:
				self.TerminateCurses()
				raise
	
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
	
	def RunImpl(self, key):
		pass
	
	def __del__(self):
		self.TerminateCurses()
		self.log.info("Oneliner curses frontend destroyed")
