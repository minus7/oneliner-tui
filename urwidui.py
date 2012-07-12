from oneliner.ui import OnelinerUIUrwid
import logging

if __name__ == "__main__":
	logging.basicConfig(format=u'[%(asctime)s] %(name)s: %(levelname)s: %(funcName)s:  %(message)s', level=logging.DEBUG, filename=u"uitest.log", filemode="w")

	o = OnelinerUIUrwid("http://www.scenemusic.net/")

	o.Run()
