import os
import sys
import socket
import uuid
import threading

current_path = sys.path[0]
exitProgram = False

def unify(string, substring = "="):
		if string.count(substring) == 0 or string.startswith("#"):
			return string
		else:
			string = string.replace(" " + substring, substring)
			string = string.replace(substring + " ", substring)
			string = string.replace(" " + substring + " ", substring)
			return string

def ini(key, value = False, path = current_path):
	if os.path.isdir(path): #If path is not a file
		path = os.path.join(path, "config.ini") #Propose a config file in that path
	available = os.path.exists(path)
	if available: #If the config file exists
		
		if isinstance(value, bool) and not value: #If this is a read operation
			with open(path, "r") as f:
				for line in f:
					dictionary = unify(line).split("=")
					if dictionary[0] == str(key):
						return str(dictionary[1]) #Return the value if it exists
				return False #Return False if it doesn't exist
			
		else: #If this is a write operation
			try:
				name = str(uuid.uuid1()).replace("-", "") + ".ini" #Create a temporary file
				temp_path = os.path.join(path, name)
				open(temp_path, "w+").close()
				temp = open(temp_path, "a")
				with open(path,"r") as f: #Open the file to be written on
					exists = False
					for line in f:
						if line.startswith("#"): #Don't process comments
							temp.write(line)
							pass
						dictionary = unify(line).split("=")
						if dictionary[0] == str(key): #If the key is to be overwritten
							exists = True
							if str(dictionary[1]) != str(value): #And its value isn't already equal to the value to be written
								temp.write(str(key) + "=" + str(value) + "\n") #Write changes
						else: #Write every other line which doesn't contain the key
							temp.write(line)
					if not exists: #If the key isn't in the file
						temp.write(str(key) + "=" + str(value) + "\n") #Add the key/value pair in
				temp.close()
				
				open(path, "w+").close() #Truncate the original file
				with open(path, "a") as f:
					with open(temp_path, "r") as temp:
						for line in temp: #Copy the temporary file to the original line by line
							f.write(str(line))
				os.unlink(temp_path) #Delete the temporary file
				return True #Return True if successful
			except Exception as e:
				print(e)
				return False
			
	else: #If the config file doesn't exist
		open(path, "w+").close() #Create the config file
		with open(path, "r+") as config:
			config.write("#Config Version 2.1" + "\n") #Comment the config version
			if not isinstance(value, bool): #If this is a write operation
				config.write(str(key) + "=" + str(value) + "\n") #Add the key/value pair in
				return True
			else: #Return False for a read operation
				return False
			
def threaded(fn):
	def wrapper(*args, **kwargs):
		thread = threading.Thread(target=fn, args=args, kwargs=kwargs)
		thread.start()
		return thread
	return wrapper
	
class File:
	class v1:
		def __init__(self, file, mode = "rb"):
			self.offset = 0 #Where the read head is
			self.requested_offset = 0 #Where the read head should move to when handling a resend request
			self.file = file
			self.buffer_size = 65536 #How many bytes to skip
			self.mode = mode
			if not os.path.exists(file):
				self.create(file)

		@staticmethod
		def create(file):
			open(file, "w+").close()

		def read(self):
			with open(self.file, self.mode, self.buffer_size) as f:
				f.seek(self.offset) #Moves the read head to where the last read operation left it
				content = f.read(self.buffer_size) #Read bytes
				self.offset += self.buffer_size #Update read head
				return content

		def write(self, data):
			with open(self.file, "ab") as f:
				f.write(data)


class Socket:

	# noinspection PyMethodParameters,PyMethodParameters
	class Multicast:
		def __init__(self):
			#Use multicast configuration
			self.sending_port = int(ini("multicast_port_send"))
			self.receiving_port = int(ini("multicast_port_receive"))
			self.multicast_address = ini("multicast_address")
			
			#Set up sending socket
			self.sending = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
			self.sending.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 1)
			
			#Set up receiving socket
			self.receiving = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
			
			#Try to make receiving address reusable
			try:
				self.receiving.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
			except AttributeError:
				pass
			
			self.receiving.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 1)
			self.receiving.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, 0)
			self.receiving.settimeout(0.1)
			self.receiving.bind(("", self.receiving_port))
			host = socket.gethostbyname(socket.gethostname())
			self.receiving.setsockopt(socket.SOL_IP, socket.IP_MULTICAST_IF, socket.inet_aton(host))
			self.receiving.setsockopt(socket.SOL_IP, socket.IP_ADD_MEMBERSHIP, socket.inet_aton(self.multicast_address) + socket.inet_aton(host))
			
			self.rx = []
		
		def send(self, data):
			self.sending.sendto(data.encode(), (self.multicast_address.encode(), self.receiving_port))
			
		#Run as daemon thread
		@threaded
		def receive(self):
			isEmpty = False
			while not isEmpty:
				try:
					d, addr = self.receiving.recvfrom(4096)
					data = d.decode()
					if data != "" or data is None:
						self.rx.append(data)
					else:
						isEmpty = True
				except socket.timeout:
					isEmpty = True

	class Tcp:
		"""
		Client connects on TX, accepts connection on RX, sends data on TX
		"""
		rx = []
		host = ini("tcp_host")
		ports = (ini("tcp_client_tx"), ini("tcp_client_rx")) #[0] Client TX, [1] Client RX
		sockets = []
		mode = ini("tcp_mode")
		def __init__(self, mode = mode, host = host, ports = ports):
			self.mode = mode
			self.host = host
			self.ports = ports
			self.sockets.append(socket.socket(socket.AF_INET, socket.SOCK_STREAM))
			self.sockets.append(socket.socket(socket.AF_INET, socket.SOCK_STREAM))
			
			if mode == "client":
				self.sockets[0].connect((self.host, self.ports[0]))
				self.sockets[1].bind((ini("tcp_localhost"), self.ports[1]))
				self.sockets[1].listen(1)
				receiver, receiver_address = self.sockets[1].accept()
				self.receiver = receiver
				self.receiver_address = receiver_address
				
			elif mode == "server":
				self.sockets[0].bind((ini("tcp_localhost"), self.ports[0]))
				self.sockets[0].listen(1)
				receiver, receiver_address = self.sockets[0].accept()
				self.receiver = receiver
				self.receiver_address = receiver_address
				self.sockets[1].connect((self.receiver_address, self.ports[1]))
		
		def sendall(self, data):
			if self.mode == "server":
				self.sockets[1].sendall(data)
			elif self.mode == "client":
				self.sockets[0].sendall(data)
				
		def recv(self, buffer = 4096):
			if self.mode == "server":
				self.rx += self.sockets[0].recv(buffer)
			elif self.mode == "client":
				self.rx += self.sockets[1].recv(buffer)

class FileHandler(File.v1):
	def __init__(self, file_dir, mode):
		super()
		super().__init__(file_dir,mode)
		self.hash_buffer = []

class Share:
	def __init__(self):
		self.file_handlers = {}

	def share(self):
		pass


multicastHandler = Socket.Multicast()
multicastReceiver = multicastHandler.receive()
doOnce = True
length = 0
testLoop = 500000
currentLoop = 0
while not exitProgram:
	#Receive data
	#multicastReceiver.join()
	if len(multicastHandler.rx) > length and doOnce:
		doOnce = False
		length = len(multicastHandler.rx)
		print(multicastHandler.rx)
	
	if currentLoop == testLoop:
		print(str(testLoop) + " loops done")
		currentLoop = 0
		
	currentLoop += 1