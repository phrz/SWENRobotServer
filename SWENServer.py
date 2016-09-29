from SWENBonjour import *
import asyncio
import websockets
import json
import uuid

class SWENServer(object):

	SERVER_BONJOUR_TYPE = '_http._tcp.local.'
	SERVER_BONJOUR_NAME_PART = 'SWENServer'
	SERVER_BONJOUR_NAME = SERVER_BONJOUR_NAME_PART + '.' + SERVER_BONJOUR_TYPE
	SERVER_PORT = 9999

	def __init__(self, bonjour):
		self._bonjour = bonjour
		self._clients = {}

	def start(self):
		print('Starting server...')
		self._bonjour.broadcast(
			self.SERVER_BONJOUR_TYPE, 
			self.SERVER_BONJOUR_NAME,
			self.SERVER_PORT)

		print('Starting websockets...')
		start_server = websockets.serve(self.handler,'',self.SERVER_PORT)
		loop = asyncio.get_event_loop()
		loop.run_until_complete(start_server)
		loop.run_forever()

	def processRequest(self,request, ws):
		try:
			requestData = json.loads(request)
		except json.decoder.JSONDecodeError:
			return {'status':'error','type':'JSONDecodeError','data':{}}

		try:
			if 'action' in requestData and requestData['action'] == 'register':
				return self.registerRobot(ws.remote_address[0], ws.remote_address[1], requestData['data']['name'])
			elif 'action' in requestData and requestData['action'] == 'deregister':
				return self.deregisterRobot(requestData['data']['uuid'])
			elif 'action' in requestData and requestData['action'] == 'message':
				return self.messageRobot(requestData['data']['uuid'], requestData['data']['message'])
		except KeyError:
			pass

		return {'status':'error','type':'UnknownRequest','data':{}}

	def messageRobot(self, robotUUID, message):
		robotName = self._clients[robotUUID]['name']
		print()
		print('Message from "{}": {}'.format(robotName, message))
		return {'status':'success','type':'SentMessage','data':{'uuid': robotUUID}}

	def registerRobot(self, address, port, name):
		robotUUID = str(uuid.uuid4())
		self._clients[robotUUID] = {'name': name, 'address': address, 'port': port}
		print('Registered robot at {}:{} (Name: {}, UUID: {})'.format(address, port, name, robotUUID))
		print()
		print('Clients:')
		print(self._clients)
		print()
		return {'status':'success','type':'RegisteredRobot','data':{'uuid': robotUUID}}

	def deregisterRobot(self, robotUUID):
		del self._clients[robotUUID]
		print('Deregistered robot {}'.format(robotUUID))
		print()
		print('Clients:')
		print(self._clients)
		print()
		return {'status':'success','type':'DeregisteredRobot','data':{'uuid': robotUUID}}

	async def producer(self, client):
		# print("producer(client:",client.remote_address[0],")")
		pass

	async def consumer(self, data):
		# print('Got',data)
		pass

	async def handler(self, ws, path):
		try:
			while True:
				inputTask = asyncio.ensure_future(ws.recv())
				outputTask = asyncio.ensure_future(self.producer(ws))
				done, pending = await asyncio.wait(
					[inputTask, outputTask],
					return_when = asyncio.FIRST_COMPLETED
				)

				await inputTask
				await self.consumer(inputTask.result())

				request = inputTask.result()
				response = self.processRequest(request, ws)

				# await outputTask
				# await ws.send(outputTask.result())
				await ws.send(json.dumps(response))

		except websockets.exceptions.ConnectionClosed:
			pass

