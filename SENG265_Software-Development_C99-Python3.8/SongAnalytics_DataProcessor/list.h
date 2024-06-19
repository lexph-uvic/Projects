/** @file list.h
 *  @brief Function prototypes for the linked list.
 */
#ifndef _LINKEDLIST_H_
#define _LINKEDLIST_H_

#include <time.h>
#define MAX_WORD_LEN 50

/**
 * @brief An struct that represents a song record node in the linked list.
 */
typedef struct node_t
{
    char track_name[200];
    char artist[200];
    unsigned int artist_count;
    struct tm date_;
    unsigned long in_spotify_playlists;
    unsigned long streams;
    unsigned long in_apple_playlists;
    struct node_t *next;
} node_t;


/**
 * Function protypes associated with a linked list.
 */
node_t *new_node();
void fill_node(node_t *, char*, unsigned int);
node_t *add_front(node_t *, node_t *);
node_t *add_end(node_t *, node_t *);
int compare_by_streams(node_t *a, node_t *b, int order);
int compare_by_apple_playlists(node_t *a, node_t *b, int order);
int compare_by_spotify_playlists(node_t *a, node_t *b, int order);
node_t *add_inorder(node_t *list, node_t *new, int (*compare)(node_t *, node_t *, int), int order);
node_t *peek_front(node_t *);
node_t *remove_front(node_t *);
void apply(node_t *, void (*fn)(node_t *, void *), void *arg);

#endif
