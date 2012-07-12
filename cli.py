from oneliner import Oneliner
import logging

if __name__ == "__main__":
	logging.basicConfig(format=u'[%(asctime)s] %(name)s: %(levelname)s: %(funcName)s:  %(message)s', level=logging.DEBUG, filename=u"uitest.log", filemode="w")

	o = Oneliner("http://www.scenemusic.net/")

	while True:
		lines = o.GetNewLines()
		
		for line in lines:
			print(u"[{}] {}: {}".format(line.time, line.author, line.message))
