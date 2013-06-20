import socket
udp_ip = "192.168.0.8"
udp_port = int(5005)
doAgain = "Y"
mySocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
mySocket.connect((udp_ip, udp_port))
while doAgain == "Y":
    message = input("Enter your message")
    mySocket.send(message.encode())
    doAgain = input("Enter Y to send another")
mySocket.close
