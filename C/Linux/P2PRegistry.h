/*
 * File:   P2PRegistry.h
 * Author: Dilum Bandara
 * Created on April 11, 2009, 8:33 PM
 */

#ifndef _P2PREGISTRY_H
#define	_P2PREGISTRY_H

#define REC_BUFFER_SIZE 100		//Receiver buffer size
#define TABLE_SIZE 30           //No of peers to maintain

struct table_entry{
    char IP[15];
    int port;
    char key[8];
    unsigned char valid;
} ;

int opensocket(int portno);
void receivedata(int sockfd);
int sendreply(int sockfd, unsigned char reg, int status);
int sendpeerlist(int sockfd, char key[8]);
unsigned char checkpeertable(char key[8]);
int sendpeertable(int sockfd);

#endif	/* _P2PREGISTRY_H */

