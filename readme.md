Machine Problem #1 -  Chat

Pol, Cyril Kaye
Opetina, Patricia Nicole

How to run:
	Server
	- run the command 'python server.py <port>'. The argument <port> refers to the port number.
	
	Client
	- run the command 'python client.py <name> <addr> <port>'. <name> refers to name assigned to the client, this
	will be used to identify the client during the chat operations. <addr> on the other hand, is the inet address
	of the chat server while <port> is the port number used for the chat application (the same port used in server).
	
Implementation:

This chat application has a server and client side. It allows clients to communicate using channels, where
clients on the same channel can chat with each other. The server in this application serves as the mediator between
clients. All messages sent over the network are actually sent to the server first before the message is broadcasted
to the intended recipients.

Once a client successfully connects to the server, it can create a channel, see the available channels, or join one
where it can freely talk with other connected clients who joined the particular room as well. It is important to 
note that a client cannot initiate communication between other clients if it has not joined any rooms yet.

	Create a channel
	- the client can create a channel by sending a message '/create <name_of_channel>' to server. The server then checks
	if the channel already exists. If there is a channel that was already created with the same name, the server notifies
	the client by forwarding a message - 'Room <name_of_channel> already exists, so cannot be created.'. (The warning/infor-
	mation message are specified in script utils.py). Otherwise, the server creates the new channel and adds the client
	automatically to the channel. All members of this channel will receive the messages sent by any member.
	
	Join a channel
	- a newly connected client can enter any channel but only one channel at a time. A client can join a particular room
	by sending the message - '/join <name_of_channel>' to server. Given that the specified room exists, the server adds the client
	allowing it to communicate with others on the same channel. 
	Now, for cases when a client wants to join other channels, it can do so by requesting the server to add it to another channel,
	revoking the client's capability to communicate using the previous channel on the process. This is because any client can only be
	a part of one channel at a time.
	
	View available channels
	- Clients can view channels by sending the message - '/list' to server. The server in turn respond by forwarding the list of created
	channels. 
