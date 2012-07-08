#!/usb/bin/python3

from oneliner import Oneliner
import logging

if __name__ == "__main__":
	log = logging.getLogger("Oneliner")
	log.setLevel(logging.DEBUG)
	logFormatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
	#logHandler = logging.FileHandler("test.log")
	logHandler = logging.StreamHandler()
	logHandler.setLevel(logging.WARNING)
	#logHandler.setLevel(logging.DEBUG)
	logHandler.setFormatter(logFormatter)
	log.addHandler(logHandler)

	o = Oneliner("http://www.scenemusic.net/")

	while True:
		lines = o.GetMoreLines()
		
		for line in lines:
			print("[{}] {}: {}".format(line.time, line.author, line.message))
