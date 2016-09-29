import require_python_3
from zeroconf import ServiceBrowser, Zeroconf, ServiceInfo
import socket
import struct

"""A class wishing to receive updates
from the Bonjour class"""
class Subscriber(object):

	def __init__(self):
		self._subscriptions = set()

	def subscriberUpdate(self, instance, message, data):
		"""Bonjour() will call this on each
		of its registered subscribers"""
		pass

	def subscribeTo(self, instance):
		# subscribe to the instance.
		instance.registerSubscriber(self)
		self._subscriptions.add(instance)

	def unsubscribeFrom(self, instance):
		instance.deregisterSubscriber(self)
		self._subscriptions.remove(instance)


"""A class inherited by Bonjour() to send
updates to its subscribers"""
class Publisher(object):

	def __init__(self):
		self._subscribers = set()

	def registerSubscriber(self, subscriber):
		self._subscribers.add(subscriber)

	def deregisterSubscriber(self, subscriber):
		self._subscribers.remove(subscriber)

	def broadcastToSubscribers(self, message, data={}):
		for sub in self._subscribers:
			sub.subscriberUpdate(self, message, data)


"""A class that simplifies zeroconf
broadcasting and discovery (wraps
`zeroconf`)"""
class Bonjour(Publisher):

	SERVICE_ADDED_MESSAGE = 'edu.smu.swen.bonjour.serviceAdded'
	SERVICE_REMOVED_MESSAGE = 'edu.smu.swen.bonjour.serviceRemoved'

	def __init__(self):
		self._zeroconf = None
		self._browser = None
		self._handler = Bonjour.ZeroconfHandler(self)
		super().__init__()

	# Handle events from Zeroconf
	class ZeroconfHandler(object):
		def __init__(self, publisher):
			self._publisher = publisher

		def add_service(self, zeroconf, type, name):
			info = zeroconf.get_service_info(type, name)
			data = {
				'name': name,
				'type': type,
				'port': info.port,
				'server': info.server,
				'properties': info.properties
			}
			self._publisher.broadcastToSubscribers(
				self._publisher.SERVICE_ADDED_MESSAGE, data)

		def remove_service(self, zeroconf, type, name):
			data = {
				'name': name,
				'type': type
			}
			self._publisher.broadcastToSubscribers(
				self._publisher.SERVICE_REMOVED_MESSAGE, data)

	# broadcast a service with a given name
	def broadcast(self, type, name, port, properties={}):
		if self._zeroconf is None:
			self._zeroconf = Zeroconf()

		# generate a short integer IP address
		# from this system's hostname
		hostname = socket.gethostname()
		host = socket.gethostbyname(hostname)

		# AF_INET => IPv4
		packedIp = socket.inet_pton(socket.AF_INET, host)

		# ServiceInfo(type_, name, address=None, port=None, weight=0,
    	#			  priority=0, properties=None, server=None)

		info = ServiceInfo(type, name, 
							address=packedIp,
							port=port, 
							properties=properties, 
							server=hostname)

		self._zeroconf.register_service(info)

	def stopBroadcast(self):
		self._zeroconf.unregister_all_services()

	# find a Bonjour service of a specific type
	def find(self, type):
		if self._zeroconf is None:
			self._zeroconf = Zeroconf()

		self._browser = ServiceBrowser(self._zeroconf, type, self._handler)

	def stop(self):
		if self._zeroconf is not None:
			self._zeroconf.close()
		self._zeroconf = None
		self._browser = None

