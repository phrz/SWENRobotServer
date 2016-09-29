from SWENBonjour import *
from SWENServer import SWENServer

if __name__ == "__main__":
	print('SWEN SERVER')
	print('=============================')

	bonjour = Bonjour()
	server = SWENServer(bonjour)

	print('Broadcasting on Bonjour...')

	try:
		server.start()
		input("Press enter to exit...\n\n")
	except KeyboardInterrupt:
	    bonjour.stopBroadcast()