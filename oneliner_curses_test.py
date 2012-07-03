from oneliner_curses import OnelinerCurses
import logging

if __name__ == "__main__":
	logFormatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
	#logHandler = logging.FileHandler("test.log")
	logHandler = logging.StreamHandler()
	logHandler.setLevel(logging.WARNING)
	#logHandler.setLevel(logging.DEBUG)
	logHandler.setFormatter(logFormatter)
	log = logging.getLogger("Oneliner")
	log.setLevel(logging.DEBUG)
	log.addHandler(logHandler)
	logC = logging.getLogger("OnelinerCurses")
	logC.setLevel(logging.DEBUG)
	logC.addHandler(logHandler)

	o = OnelinerCurses("http://www.scenemusic.net/")

	o.Run()