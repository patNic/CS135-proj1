
import sys
import socket
import select
import utils

list_of_channels = []
list_of_channel_names = []
 
response = None   
SOCKET_LIST = []


def main(argv):
   
    if(len(sys.argv) != 2):
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
                    request = sock.recv(200)

                    while len(request) != utils.MESSAGE_LENGTH and len(request) > 0:
                        request = request + sock.recv(utils.MESSAGE_LENGTH - len(request))

                    request = request.strip()
                    if request:
                        if request.startswith("/list"):
                            sendLists(sock)
                        elif request.startswith("/name"):
                            name = request.replace("/name", "")
                            print "[INFO] New client " + name + " connected"
                        elif request.startswith("/create"):
                            channel = request.replace("/create", "")
                            name = channel[channel.index("["):channel.index("]")+1]
                            channel = channel.replace(name, "").replace(" ", "").replace("\n", "")
                            createChannel(channel, sock, name)
                        elif request.startswith("/join"):
                            join = request.replace("/join", "")
                            name = ''

                            if "[" in join and "]" in join:
                                name = join[join.index("["):join.index("]")+1]
                                join = join.replace(name, "").replace("\n", "")

                            join = join.strip()
                            joinChannel(join, sock, name)
                        else:
                            if handle_request_exceptions(request, sock):
                                broadcast(request, sock, False, False)
                    else:
                        # remove the socket that's broken
                        print "[INFO] A client was disconnected ..."

                        if sock in SOCKET_LIST:
                            #broadcast(request, sock, True, True)
                            previous_channel = check_if_in_channel(sock)
                            if(previous_channel[0]):
                                transfer_to_new_channel(sock, previous_channel[1])
                                
                            SOCKET_LIST.remove(sock)
                except Exception as e:
                    print(repr(e))
     
    server_socket.close()             
    return


def broadcast(message, socket, bool, is_client_down):

    sender_details = determine_channel(socket)

    if sender_details != None:
        members = sender_details[0]

        if is_client_down:
            client_name = sender_details[1]
            message = utils.SERVER_CLIENT_LEFT_CHANNEL.format(client_name[1:len(client_name)-1]) + "\n"
        if members != None:
            for client in members:
                if(client != socket):
                    if bool:
                        client.send(pad_message(message))
                    else:
                        client.send(pad_message(sender_details[1] + " " + message))
    return


def pad_message(message):
    while len(message) < utils.MESSAGE_LENGTH:
        message += " "
    
    return message[:utils.MESSAGE_LENGTH]


def check_if_in_channel(sock):
    for channel in list_of_channels:
        members = channel.get_clients()

        if sock in members:
            return [True, channel]

    return [False, None]


def send_message_specific_client(message, socket):
    try :
        socket.send(pad_message(message))
    except :
        # broken socket connection
        socket.close()
        # broken socket, remove it
        if socket in SOCKET_LIST:
            #broadcast(request, sock, True, True)
            previous_channel = check_if_in_channel(sock)
            if(previous_channel[0]):
                transfer_to_new_channel(socket, previous_channel[1])
                                   
            SOCKET_LIST.remove(socket)
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
    print "[INFO] A client is asking for the list of channels ... "
    response = '\n    '.join(list_of_channel_names)
    try :
        if len(list_of_channel_names) > 0:
            socket.send(pad_message(response))
        else:
            socket.send(pad_message(response))
    except :
        # broken socket connection
        socket.close()
        # broken socket, remove it
        if socket in SOCKET_LIST:
            #broadcast(request, sock, True, True)
            previous_channel = check_if_in_channel(sock)
            if(previous_channel[0]):
                transfer_to_new_channel(socket, previous_channel[1])
                
            SOCKET_LIST.remove(socket)
    return

    
def createChannel(channel_name, socket, name):
    
    if len(channel_name) == 0:
        error_message = utils.SERVER_CREATE_REQUIRES_ARGUMENT
        send_message_specific_client(error_message+"\n", socket)
    else:
        if channel_name in list_of_channel_names:
            error_message = utils.SERVER_CHANNEL_EXISTS.format(channel_name)
            send_message_specific_client(error_message+"\n", socket)
        else:
            previous_channel = check_if_in_channel(socket)
            if previous_channel[0]:
                transfer_to_new_channel(socket, previous_channel[1])

            print "[INFO] New channel created: " + channel_name
            new_channel = Channel(channel_name, [socket], [name])
            list_of_channels.append(new_channel)
            list_of_channel_names.append(new_channel.get_name())

    return


def transfer_to_new_channel(socket, channel):
    ind = channel.get_clients().index(socket)
    channel.get_clients().remove(socket)
    name1 = channel.get_chat_mates()[ind]
    channel.get_chat_mates().remove(name1)

    for client in channel.get_clients():
        client.send(pad_message(utils.SERVER_CLIENT_LEFT_CHANNEL.format(name1[1:len(name1) - 1]) + "\n"))


def joinChannel(channel_name, socket, name):
    is_channel_exists = False
    previous_channel = check_if_in_channel(socket)
    if previous_channel[0]:
        transfer_to_new_channel(socket, previous_channel[1])

    for channel in list_of_channels:
        if channel.get_name() == channel_name:
            channel.add_client(socket, name)
            is_channel_exists = True
    
    if not is_channel_exists:
        handle_join_exceptions(channel_name, socket, name)
    else:
        print "[INFO] New client joined : " + channel_name
        info_message = utils.SERVER_CLIENT_JOINED_CHANNEL.format(name[1:len(name)-1])
        broadcast(info_message+"\n", socket, True, False)
    return


def handle_join_exceptions(channel_name, socket, name):
    if len(channel_name) == 0:
        error_message = utils.SERVER_JOIN_REQUIRES_ARGUMENT
    else:
       
        error_message = utils.SERVER_NO_CHANNEL_EXISTS.format(channel_name[:len(channel_name)])
    send_message_specific_client(error_message+"\n", socket)  
    
    return

def handle_request_exceptions(request, sock):
    if request.startswith("/"):
        error_message = utils.SERVER_INVALID_CONTROL_MESSAGE.format(request[:len(request)])
        send_message_specific_client(error_message+"\n", sock)
        return False
    else:
        socket_detail = determine_channel(sock)
        if not socket_detail:
            error_message = utils.SERVER_CLIENT_NOT_IN_CHANNEL
            send_message_specific_client(error_message+"\n", sock)
            return False
    return True

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
