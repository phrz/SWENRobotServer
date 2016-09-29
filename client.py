from SWENBonjour import *
import asyncio
import websockets
import json

class SWENClient(Subscriber):

	ROBOT_NAME = 'Heptahedron'

	def __init__(self, bonjour):
		super().__init__()
		self._bonjour = bonjour
		self.subscribeTo(self._bonjour)
		self.serverInfo = None
		self.connected = False
		self._uuid = None

	# proto Subscriber
	def subscriberUpdate(self, instance, message, data):
		if(message == 'edu.smu.swen.bonjour.serviceAdded' 
		and data['name'] == 'SWENServer._http._tcp.local.'):
			self.connected = True
			self.serverInfo = data

	async def hello(self):
		server = self.serverInfo['server'].rstrip('.')
		port = self.serverInfo['port']
		address = 'ws://{}:{}'.format(server, port)
		print('Connecting to', address)
		try:
			async with websockets.connect(address) as websocket:
				try:
					while True:
						sendData = input("$ ")
						await websocket.send(sendData)
						responseData = await websocket.recv()
						print("{}".format(responseData))

				except websockets.exceptions.ConnectionClosed:
					pass
				finally:
					print('Closing websockets test...')
		except OSError:
			print('[Connection error]')

	async def registerClient(self):
		server = self.serverInfo['server'].rstrip('.')
		port = self.serverInfo['port']
		address = 'ws://{}:{}'.format(server, port)
		print('Connecting to', address)
		try:
			async with websockets.connect(address) as websocket:
				try:
					request = json.dumps({'action':'register','data':{'name': self.ROBOT_NAME}})
					await websocket.send(request)
					responseData = await websocket.recv()
					response = json.loads(responseData)

					self._uuid = response['data']['uuid']
					print("\nAssigned UUID: {}".format(self._uuid))

				except websockets.exceptions.ConnectionClosed:
					pass
		except OSError:
			print('[Connection error]')

	async def deregisterClient(self):
		server = self.serverInfo['server'].rstrip('.')
		port = self.serverInfo['port']
		address = 'ws://{}:{}'.format(server, port)
		try:
			async with websockets.connect(address) as websocket:
				try:
					request = json.dumps({'action':'deregister','data':{'uuid': self._uuid}})
					await websocket.send(request)
					responseData = await websocket.recv()
					response = json.loads(responseData)

				except websockets.exceptions.ConnectionClosed:
					pass
		except OSError:
			print('[Connection error]')

	async def sendMessage(self, message):
		server = self.serverInfo['server'].rstrip('.')
		port = self.serverInfo['port']
		address = 'ws://{}:{}'.format(server, port)
		try:
			async with websockets.connect(address) as websocket:
				try:
					request = json.dumps({'action':'message','data':{'message': message, 'uuid': self._uuid}})
					await websocket.send(request)
					responseData = await websocket.recv()
					response = json.loads(responseData)

				except websockets.exceptions.ConnectionClosed:
					pass
		except OSError:
			print('[Connection error]')

if __name__ == "__main__":
	print('SWEN CLIENT')
	print('=============================')

	print('Searching for server over Bonjour...')

	bonjour = Bonjour()
	client = SWENClient(bonjour)
	bonjour.find('_http._tcp.local.')

	while not client.connected:
		pass

	print('Found the server at "{}" port {}'.format(client.serverInfo['server'].rstrip('.'), client.serverInfo['port']))

	loop = asyncio.get_event_loop()
	try: 
		print('Registering client...')
		loop.run_until_complete(client.registerClient())
		print('[Press Ctrl+C to exit]')
		while True:
			message = input('msg > ')
			loop.run_until_complete(client.sendMessage(message))
	except KeyboardInterrupt:
		loop.run_until_complete(client.deregisterClient())



