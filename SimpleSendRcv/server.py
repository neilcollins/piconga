import socket
udp_port = int(5005)
mySocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
mySocket.bind(("", udp_port))
mySocket.listen(2)
while 1:
	client_sock, addr = mySocket.accept()
	while 1:
		data = client_sock.recv(1024)
		print ("Message is", data)
mySocket.close()
