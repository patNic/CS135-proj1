'''
Created on 4 Feb 2019

@author: Kaye
'''
import sys
import socket
import select
    
list_of_channels = []
list_of_channel_names = []
 
response = None   
SOCKET_LIST = []


def main(argv):

    if len(sys.argv) != 2:
        print "Please supply a port number."
        sys.exit()        
    port_number = int(sys.argv[1])   
                
    server('localhost', port_number)
    return


def server(host, port):
    print "[INFO] Server waiting for connections ..."

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((host, port))
    server_socket.listen(10)
 
    # add server socket object to the list of readable connections
    SOCKET_LIST.append(server_socket)
    
    while 1:
        ready_to_read,ready_to_write,in_error = select.select(SOCKET_LIST,[],[],0)
        
        for sock in ready_to_read:
            if sock == server_socket:
                sockfd, addr = server_socket.accept()
                SOCKET_LIST.append(sockfd)
            else:
                try:
                    request = sock.recv(1024)
                  
                    if request:
                        if request.startswith("/list"):
                            sendLists(sock)
                        elif request.startswith("/name"):
                            name = request.replace("/name", "")
                            print "[INFO] New client " + name + " connected"
                        elif request.startswith("/create"):
                            channel = request.replace("/create", "")
                            name = channel[channel.index("["):channel.index("]")+1]
                            channel = channel.replace(name+" ", "").replace("\n", "")
                            createChannel(channel, sock, name)
                        elif request.startswith("/join"):
                            join = request.replace("/join", "")
                            name = join[join.index("["):join.index("]")+1]
                            print name
                            join = join.replace(name, "").replace(" ", "").replace("\n", "")
                            joinChannel(join, sock, name)
                        else:
                            broadcast(request, sock)
                    else:
                        # remove the socket that's broken  
                        if sock in SOCKET_LIST:
                            SOCKET_LIST.remove(sock)
                except Exception as e:
                    print(e)
     
    server_socket.close()             
    return


def broadcast(message, socket):
    sender_details = determine_channel(socket)
    members = sender_details[0]

    if members:
        for client in members:
            if client != socket:
                client.send(sender_details[1] + ":" + message)
    return


def determine_channel(socket):
    for channel in list_of_channels:
        members = channel.get_clients()

        if socket in members:
            ind = members.index(socket)
            sender = channel.chat_mates[ind]
            return [members, sender]

    return None


def sendLists(socket):
    response = '\n'.join(list_of_channel_names)
    try :
        socket.send(response+"\n")
    except :
        # broken socket connection
        socket.close()
        # broken socket, remove it
        if socket in SOCKET_LIST:
            SOCKET_LIST.remove(socket)
    return


def createChannel(channel_name, socket, name):
    
    print "[INFO] New channel created: " + channel_name
    new_channel = Channel(channel_name, [socket], [name])
    list_of_channels.append(new_channel)
    list_of_channel_names.append(new_channel.get_name())
    
    return


def joinChannel(channel_name, socket, name):
    for channel in list_of_channels:
        if channel.get_name() == channel_name:
            channel.add_client(socket, name)
    print "[INFO] Client "+ name + " joined : " + channel_name
    return


class Channel:
    
    def __init__(self, name, clients, chat_mates):
        self.name = name
        self.clients = clients
        self.chat_mates = chat_mates

    def get_name(self):
        return self.name

    def add_client(self, socket, name):
        self.clients.append(socket)
        self.chat_mates.append(name)

    def get_clients(self):
        return self.clients

    def get_chat_mates(self):
        return self.chat_mates


if __name__ == '__main__':
    main(sys.argv[0:1])
