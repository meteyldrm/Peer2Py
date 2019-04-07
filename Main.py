import time
import os
import sys
import socket
import uuid

def unify(string, substring = "="):
		if string.count(substring) == 0 or string.startswith("#"):
			return string
		else:
			string = string.replace(" " + substring, substring)
			string = string.replace(substring + " ", substring)
			string = string.replace(" " + substring + " ", substring)
			return string

current_path = sys.path[0]

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

class File:
	def __init__(self, file, mode = "rb"):
		self.offset = 0 #Where the read head is
		self.buffer_size = 4096 #How many bytes to skip
		self.requested_offset = 0 #Where the read head should move to when handling a resend request
		self.file = file
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
	#Update class to use init for receiving
	class Broadcast:
		def send(data):
			sending = ini("broadcast_port_send")
			receiving = ini("broadcast_port_receive")
			broadcast_address = ini("broadcast_address")
			
			s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
			s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
			s.settimeout(0.2)
			s.bind((broadcast_address, sending))
			s.sendto(data.encode() ,(broadcast_address.encode(), receiving))
			
		#Rewrite
		@staticmethod
		def receive():
			receiving = ini("broadcast_port_receive")
			
			s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
			s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
			s.bind(("", receiving))
			while True:
				d, addr = s.recvfrom(4096)
				data = d.decode()
				print(data)
	
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

