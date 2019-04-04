import time
import os
import sys
import socket
import uuid

def ini(key, value = False, path = False):
	return Data.ini(key, value, path)

def unify(string, substring = "="):
		if string.count(substring) == 0 or string.startswith("#"):
			return string
		else:
			string = string.replace(" " + substring, substring)
			string = string.replace(substring + " ", substring)
			string = string.replace(" " + substring + " ", substring)
			return string

class Data:
	path = sys.path[0]
	def ini(self, key, value = False, path = sys.path[0]):
		if isinstance(path, bool) and not path:
			path = os.path.join(self.path, "config.ini")
		available = os.path.exists(path)
		if available:
			if isinstance(value, bool) and not value:
				with open(path, "r") as f:
					for line in f:
						dictionary = unify(line).split("=")
						if dictionary[0] == str(key):
							return str(dictionary[1])
					return False
			else:
				try:
					name = str(uuid.uuid1()).replace("-", "") + ".ini"
					temp_path = os.path.join(self.path, name)
					open(temp_path, "w+").close()
					temp = open(temp_path, "a")
					with open(path,"r") as f:
						exists = False
						for line in f:
							if line.startswith("#"):
								temp.write(line)
								pass
							dictionary = unify(line).split("=")
							if dictionary[0] == str(key):
								exists = True
								if str(dictionary[1]) != str(value):
									temp.write(str(key) + "=" + str(value) + "\n")
							else:
								if not line.startswith("#"):
									temp.write(line)
						if not exists:
							temp.write(str(key) + "=" + str(value) + "\n")
					temp.close()
					open(path, "w+").close()
					with open(path, "a") as f:
						with open(temp_path, "r") as temp:
							for line in temp:
								f.write(str(line))
					os.unlink(temp_path)
					return True
				except Exception as e:
					print(e)
					return False
		else:
			open(path, "w+").close()
			with open(path, "r+") as config:
				config.write("#Config Version 2.1" + "\n")
				if not isinstance(value, bool):
					config.write(str(key) + "=" + str(value) + "\n")
				else:
					return False

class Socket:
	# noinspection PyMethodParameters,PyMethodParameters
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

