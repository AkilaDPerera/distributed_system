
/*
 * File:   P2PRegistry.cpp
 * Author: Dilum Bandara
 * Created on April 11, 2009, 8:21 PM
 */

#include <stdlib.h>
#include <stdio.h>
#include <errno.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <sys/socket.h>
#include <sys/types.h>
#include <string.h>
#include "P2PRegistry.h"
#include <netdb.h>


struct table_entry peer_table[TABLE_SIZE];
int no_peers = 0;

int main(int argc, char** argv)
{
    int portno; //Port number
    int retval; //Return value
    int socket_fd; //Socket file descripter

    if (argc != 2)
    {
        printf("Incorrect command format.\nShould be similar to P2PRegistory <port no>\n");
        exit(1); // exit with error
    }

    retval = sscanf(*(++argv), "%d", &portno); //check whether the given port no is within the valid range
    if (retval <= 0 || !(portno >= 1024 && portno <= 65535))
    {
        printf("Invalid port number. Port number should be between 1024-65535\n");
        exit(1); // exit with error
    }

    socket_fd = opensocket(portno);
    while (1)
        receivedata(socket_fd);
    return (EXIT_SUCCESS);
}

/*--------------------------------------------------------------------------------------------------------------*
 * 	This function creates a socket on the given port.                               							*
 *	Input - Port No                                                                                   			*
 *	Return - Socket file  descriptor. Retrun 0 in case of error                  								*
 *--------------------------------------------------------------------------------------------------------------*/
int opensocket(int portno)
{
    int sockfd;
    int retval;
    struct sockaddr_in myaddress;
    char *msgtodisplay, *tmpmsg; //Message to be displayed
    int recbufsize, sockoptsize;

    myaddress.sin_family = AF_INET;
    myaddress.sin_port = htons(portno); //Convert to network byte order
    //myaddress.sin_addr.s_addr = inet_addr("127.0.0.1");
    myaddress.sin_addr.s_addr = INADDR_ANY; // Use any of the available addresses
    memset(&(myaddress.sin_zero), 0, 8); // Make last 8 bytes 0

    sockfd = socket(PF_INET, SOCK_STREAM, 0); // Open a TCP socket
    if (sockfd == 0) // if error while creating a socket
    {
        printf("Unable to open a socket on port %d ......\n", portno);
        perror("");
        exit(1); //exit with error
    }

    //bind to port
    retval = bind(sockfd, (struct sockaddr *) & myaddress, sizeof (struct sockaddr));
    if (retval == -1) // if error while binding the socket
    {
        perror("Can't bind to the port......");
        printf("%s\n", strerror(errno));
        exit(1); //exit with error
    }
    printf("Socket created..... \n");

    //Start listening for client connections
    retval = listen(sockfd, 5);
    if (retval == -1) // if error while listening
    {
        printf("Unable to listen on port %d ......\n", portno);
        perror("");
        exit(1); //exit with error
    }
    printf("Listening on port %d..............\n", portno);
    return sockfd;
}

/*------------------------------------------------------------------------------------------------------------------*
 * 	This function listen to new peers that are trying to connect to the system										*
 *	sockfd - Socket descripter                                                                               		*
 *       nopeers - no of peers entries to maintain in table                                           				*
 *	Return - None                                                                                                  	*
 *------------------------------------------------------------------------------------------------------------------*/
void receivedata(int sockfd)
{
    char rec_buffer[REC_BUFFER_SIZE]; //allocate buffer to receive maximum possible data
    socklen_t addresslen;
    int connectedsocket;
    int numbytesrec, msglength;
    int retval;
    struct sockaddr_in senderaddress; //Use to hold the sender's address
    char *string_token;

     memset (rec_buffer,0,REC_BUFFER_SIZE);    //Clear the receiver buffer

    /* Accept connections from peers.
     * For future communication connectedsocket id will be used */
    addresslen = sizeof (struct sockaddr);
    connectedsocket = accept(sockfd, (struct sockaddr *) & senderaddress, &addresslen);
    if (connectedsocket == -1) //If error while accepting
    {
        printf("Error while accepting client ......\n");
        perror("");
    }
    printf("Conncted from: %s\n", inet_ntoa(senderaddress.sin_addr));

    numbytesrec = recv(connectedsocket, rec_buffer, 5, 0); //Read only the length of the message
    if (numbytesrec == -1) //In case of error
    {
        perror("Error while receiving data");
        perror("");
        exit(1);
    }

    string_token = strtok(rec_buffer, " "); //Break at the first space
    msglength = atoi(string_token);
    if(msglength < 8)
    {
        printf("In correct command format. Sending ERROR message to peer...\n");
        retval = sendreply(connectedsocket, 1, -4);
        if (retval < 1)
            printf("Error sending responce back to peer\n");
        close(connectedsocket); //close the connected soocket
        return;
    }

    numbytesrec = recv(connectedsocket,  rec_buffer, (msglength - 5), 0); //Read rest of the message
    if (numbytesrec == -1) //In case of error
    {
        perror("Error while receiving data");
        perror("");
        exit(1);
    }

    printf("COMMAND: %s\n", rec_buffer);
    string_token = strtok(rec_buffer, " "); //Break at the 2nd space, IP address
    if (strcmp("REG", string_token) == 0) //Check whether the command is valid.
    {
        unsigned char invalid = 0;
        unsigned char already_in = 0;
        if (no_peers < TABLE_SIZE)
        {
            int i;
            for (i = 0; i < TABLE_SIZE; i++) //Repeat until find a free slot in table
            {
                if (peer_table[i].valid == 0)
                    break;
            }

            string_token = strtok(NULL, " "); //Break at the 3rd space, IP address
            if (string_token != NULL)
                strcpy(peer_table[i].IP, string_token);
            else
                invalid = 1;

            string_token = strtok(NULL, " "); //Break at the 4th  space, port no
            if (string_token != NULL)
            {
                peer_table[i].port = atoi(string_token);
                if((peer_table[i].port < 1) || (peer_table[i].port > 65535))    //In correct port number
                    invalid = 1;
            }
            else
                invalid = 1;

            string_token = strtok(NULL, " "); //Break at the 5th space, key
            if (string_token != NULL)
            {
                if (checkpeertable(string_token) == 0)
                    strcpy(peer_table[i].key, string_token);
                else
                    already_in = 1;
           }
            else
                invalid = 1;

            if (already_in == 1)
            {
                printf("Already in peer table....\n");
                retval = sendreply(connectedsocket, 1, -1); //Indicate failure to peer
                if (retval < 1)
                    printf("Error sending responce back to peer\n");
            }
            else if ((invalid == 0) && (already_in == 0))   //If all entries are valid
            {
                peer_table[i].valid = 1;
                no_peers++;
                retval = sendpeerlist(connectedsocket, peer_table[i].key); //Indicate sucess to peer
                if (retval < 1)
                    printf("Error sending responce back to peer\n");
            }
            else if((invalid == 1) && (already_in == 0))
            {
                printf("Invalid IP, port number or, key....\n");
                retval = sendreply(connectedsocket, 1, -2); //Indicate failure to peer
                if (retval < 1)
                    printf("Error sending responce back to peer\n");
            }
        }
        else
        {
            printf("Peer table full....\n");
            sendreply(connectedsocket, 1, -3); //Indicate table full
            if (retval < 1)
                printf("Error sending responce back to peer\n");
        }
    }
    else if (strcmp("UNREG", string_token) == 0) //Check whether the command is valid.
    {
        int i;
        string_token = strtok(NULL, " ");   //Break at the 3rd space
		string_token = strtok(NULL, " ");   //Break at the 4th space
		string_token = strtok(NULL, " ");   //Break at the 5th space
        for (i = 0; i < TABLE_SIZE; i++)
        {
            if ((strncmp(peer_table[i].key, string_token, 8) == 0) && (peer_table[i].valid == 1))
            {
                peer_table[i].valid = 0;
                no_peers--;
                break;
            }
        }
        if (i < TABLE_SIZE)
            retval = sendreply(connectedsocket, 0, 0); //Unregistration sucessful
        else
            retval = sendreply(connectedsocket, 0, -1); //Unregistration unsucessful. No entry in table
        if (retval < 1)
            printf("Error sending responce back to peer\n");
    }
    else if (strcmp("PRINT", string_token) == 0) //Check whether the command is valid.
    {
        retval = sendpeertable(connectedsocket);
        if (retval < 1)
            printf("Error sending peer list.....\n");
    }
    else
    {
        printf("Invalid command\n");
        sendreply(connectedsocket, 1, -4); //Indicate invalid command
        if (retval < 1)
            printf("Error sending responce back to peer\n");
    }
    close(connectedsocket); //close the connected soocket
}

/*------------------------------------------------------------------------------------------------------------------*
 * 	This function will send the list of existing peers to the new peer      										*
 *	sockfd - Socket descripter                                                                         				*
 *      reg - whether it's a registration request or not                                         					*
 *      status - 0 - Uncessful, 1 - sucessful                                                            			*
 *	Return - Number of bytes send                                                                  					*
 *      key - Key of the new peer.                                                                          		*
 *------------------------------------------------------------------------------------------------------------------*/
int sendpeerlist(int sockfd, char key[8])
{
    char message[1000], tmpmsg[100], tmpmsglen[4];
    int msglen, numbytessend, retvalue, i, j;
    msglen = numbytessend = 0;

    if(no_peers == 1)
    {
        strcpy(message, "0012 REGOK 0");
        msglen = 12;
    }
    else
    {
        retvalue = sprintf(message, "0000 REGOK %d", (no_peers - 1));
        if(no_peers <= 10) //only 9 peers will be send if there are 10. Skip own entry
            msglen = 12;
        else if(no_peers <= 100) // only 99 peers will be send.
            msglen = 13;
        else if(no_peers <= 1000)
            msglen = 14;
        else
            msglen = 15;

        for(i = 0; i < no_peers; i++)
        {
            if((peer_table[i].valid == 1) && (strcmp(peer_table[i].key, key) != 0))
            {
                retvalue = sprintf(tmpmsg, " %s %d %s", peer_table[i].IP, peer_table[i].port, peer_table[i].key);
                memcpy(&message[msglen], tmpmsg, (strlen(tmpmsg) - 1));
                msglen += (strlen(tmpmsg) - 1);
            }
        }
        sprintf(tmpmsglen,"%04d", msglen); //Don't send the last zero
        message[0] = tmpmsglen[0];
        message[1] = tmpmsglen[1];
        message[2] = tmpmsglen[2];
        message[3] = tmpmsglen[3];
    }
    numbytessend = send(sockfd, message, msglen, 0);
    if(numbytessend <= 0)
        perror("ERROR: \n");
    return numbytessend;
}

/*------------------------------------------------------------------------------------------------------------------*
 * 	This function will send the list of existing peers to the new peer      										*
 *	sockfd - Socket descripter                                                                         				*
 *      reg - whether it's a registration request or not                                          					*
 *      status - 0 - Uncessful, 1 - sucessful                                                            			*
 *	Return - Number of bytes send                                                                  					*
 *------------------------------------------------------------------------------------------------------------------*/
int sendreply(int sockfd, unsigned char reg, int status)
{
    char message[1000], tmpmsg[50];
    int msglen, numbytessend, retvalue;
    msglen = numbytessend  = 0;

    if((reg == 1) && (status == -1)) //REG & already registered
    {
        strcpy(message, "0015 REGOK 9999");
        msglen = 15;
    }
    else if((reg == 1) && (status == -2)) //REG & error
    {
        strcpy(message, "0015 REGOK 9998");
        msglen = 15;
    }
    else if((reg == 1) && (status == -3)) //REG & peer table full
    {
        strcpy(message, "0015 REGOK 9997");
        msglen = 15;
    }
    else if((reg == 1) && (status == -4))   //Incorrect command or command format
    {
        strcpy(message, "0010 ERROR");
        msglen = 10;
    }
    else if((reg == 0) && (status == 0)) //UNREG sucess
    {
        strcpy(message, "0012 UNROK 0");
        msglen = 12;
    }
    else if((reg == 0) && (status == -1)) //UNREG fail
    {
        strcpy(message, "0012 UNROK 9999");
        msglen = 15;
    }

    numbytessend = send(sockfd, message, msglen, 0);
    return numbytessend;
}

/*----------------------------------------------------------------------------------------------------------------------*
 * 	This function checks whethe a given key is already in the table                										*
 *	key - Hash                                                                                                  		*
 *	Return - true if already in peer table                                                          					*
 *----------------------------------------------------------------------------------------------------------------------*/
unsigned char checkpeertable(char key[8])
{
    int i;
    for (i = 0; i < TABLE_SIZE; i++)
        if ((strncmp(peer_table[i].key, key, 8) == 0) && (peer_table[i].valid == 1))
            return 1;
    return 0;
}

int sendpeertable(int sockfd)
{
    char message[1500], tmpmsg[50];
    int msglen, numbytessend, retvalue, i;
    msglen = numbytessend  = 0;

    for (i = 0; i < TABLE_SIZE; i++)
    {
        if (peer_table[i].valid == 1)
        {
               retvalue = sprintf(tmpmsg, "%s %d %s\n", peer_table[i].IP, peer_table[i].port, peer_table[i].key);
                memcpy(&message[msglen], tmpmsg, strlen(tmpmsg));
                msglen += strlen(tmpmsg);
        }
    }
    numbytessend = send(sockfd, message, msglen, 0);
    return numbytessend;
}
