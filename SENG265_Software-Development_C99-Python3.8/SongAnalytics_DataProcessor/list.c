/** @file list.c
 *  @brief Implementation of a linked list.
 *
 * Based on the implementation approach described in "The Practice
 * of Programming" by Kernighan and Pike (Addison-Wesley, 1999).
 *
 */
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdbool.h>
#include "emalloc.h"
#include "list.h"


/** [1]
 * @brief Creates a new node.
 *
 * This function allocates memory for a new node of type node_t and returns a pointer to the newly created node. It uses the emalloc function to allocate memory and asserts that the allocation was successful.
 *
 * @return node_t* Returns a pointer to the newly created node.
 */
node_t *new_node()
{
    // Allocate space for new node
    node_t *node = (node_t *)emalloc(sizeof(node_t));
    assert(node != NULL && "node == NULL");

    return node;
}

/** [1]
 * @brief Fills a node with data from a token.
 *
 * This function takes a node, a token, and a count as input. It fills the fields of the node based on the count. The token is expected to be a string representation of the data to be filled in the node.
 *
 * @param record The node to be filled with data.
 * @param token The string representation of the data to be filled in the node.
 * @param count The index indicating which field of the node to fill.
 */
void fill_node(node_t *record, char *token, unsigned int count)
{
    
    // If token has newline character on end, remove it
    size_t len = strlen(token);
    char temp[200];

    switch (count) {
        case 0:
            strcpy(record->track_name, token); break;
        case 1:
            strcpy(record->artist, token); break;
        case 2:
            record->artist_count = atoi(token); break;
        case 3:
            record->date_.tm_year = atoi(token) - 1900; break;
        case 4:
            record->date_.tm_mon = atoi(token) - 1; break;
        case 5:
            record->date_.tm_mday = atoi(token); break;
        case 6:
            record->in_spotify_playlists = strtoul(token, NULL, 10); break;
        case 7:
            record->streams = strtoul(token, NULL, 10); break;
        case 8:
            strcpy(temp, token);
            if (len > 0 && token[len-1]=='\n') {
                temp[len - 1] = '\0';  // Remove the newline character
            }
            record->in_apple_playlists = strtoul(temp, NULL, 10); break;
        default:
            printf("Token Fetch Failed, count: %d\n", count);
    }   
}

/**
 * Function:  add_front
 * --------------------
 * @brief  Allows to add a node at the front of the list.
 *
 * @param list The list where the node will be added (i.e., a pointer to the first element in the list).
 * @param new The node to be added to the list.
 *
 * @return node_t* A pointer to the new head of the list.
 *
 */
node_t *add_front(node_t *list, node_t *new)
{
    new->next = list;
    return new;
}

/**
 * Function:  add_end
 * ------------------
 * @brief  Allows to add a node at the end of the list.
 *
 * @param list The list where the node will be added (i.e., a pointer to the first element in the list).
 * @param new The node to be added to the list.
 *
 * @return node_t* A pointer to the head of the list.
 *
 */
node_t *add_end(node_t *list, node_t *new)
{
    node_t *curr;

    if (list == NULL)
    {
        new->next = NULL;
        return new;
    }

    for (curr = list; curr->next != NULL; curr = curr->next)
        ;
    curr->next = new;
    new->next = NULL;
    return list;
}

/** [1]
 * @brief Compares two nodes based on the number of streams.
 *
 * This function compares two nodes (a and b) based on the number of streams. If order is greater than 0, it sorts in ascending order; otherwise, it sorts in descending order.
 *
 * @param a The first node to compare.
 * @param b The second node to compare.
 * @param order The order in which to sort the nodes.
 * @return int Returns 1 if a is greater than b, -1 if a is less than b, and 0 if they are equal.
 */
int compare_by_streams(node_t *a, node_t *b, int order) {
    if (order > 0) {
        return (a->streams > b->streams) - (a->streams < b->streams);
    } else {
        return (b->streams > a->streams) - (b->streams < a->streams);
    }
}

/** [1]
 * @brief Compares two nodes based on whether they are in Apple playlists.
 *
 * This function compares two nodes (a and b) based on whether they are in Apple playlists. If order is greater than 0, it sorts in ascending order; otherwise, it sorts in descending order.
 *
 * @param a The first node to compare.
 * @param b The second node to compare.
 * @param order The order in which to sort the nodes.
 * @return int Returns the difference between the number of Apple playlists in which a and b appear.
 */
int compare_by_apple_playlists(node_t *a, node_t *b, int order) {
    if (order > 0) {
        return a->in_apple_playlists - b->in_apple_playlists;
    } else {
        return b->in_apple_playlists - a->in_apple_playlists;
    }
}

/** [1]
 * @brief Compares two nodes based on whether they are in Spotify playlists.
 *
 * This function compares two nodes (a and b) based on whether they are in Spotify playlists. If order is greater than 0, it sorts in ascending order; otherwise, it sorts in descending order.
 *
 * @param a The first node to compare.
 * @param b The second node to compare.
 * @param order The order in which to sort the nodes.
 * @return int Returns the difference between the number of Spotify playlists in which a and b appear.
 */
int compare_by_spotify_playlists(node_t *a, node_t *b, int order) {
    if (order > 0) {
        return a->in_spotify_playlists - b->in_spotify_playlists;
    } else {
        return b->in_spotify_playlists - a->in_spotify_playlists;
    }
}

/**
 * @brief Inserts a new node into a sorted linked list in the correct order.
 *
 * @param list The head of the linked list.
 * @param new The new node to be inserted.
 * @param compare The comparison function used to determine the order of the nodes.
 * @param order The order in which to sort the list.
 * @return node_t* The head of the linked list.
 */
node_t *add_inorder(node_t *list, node_t *new, int (*compare)(node_t *, node_t *, int), int order) {
    // Create a new node with the same data
    node_t *new_node = malloc(sizeof(node_t));
    *new_node = *new;

    node_t *prev = NULL;
    node_t *curr = list;

    while (curr != NULL && compare(new_node, curr, order) > 0) {
        prev = curr;
        curr = curr->next;
    }

    new_node->next = curr;

    if (prev == NULL) {
        return new_node;
    } else {
        prev->next = new_node;
        return list;
    }
}


/**
 * Function:  peek_front
 * ---------------------
 * @brief  Allows to get the head node of the list.
 *
 * @param list The list to get the node from.
 *
 * @return node_t* A pointer to the head of the list.
 *
 */
node_t *peek_front(node_t *list)
{
    return list;
}

/**
 * Function:  remove_front
 * -----------------------
 * @brief  Allows removing the head node of the list.
 *
 * @param list The list to remove the node from.
 *
 * @return node_t* A pointer to the head of the list.
 *
 */
node_t *remove_front(node_t *list)
{
    if (list == NULL)
    {
        return NULL;
    }

    return list->next;
}

/**
 * Function: apply
 * --------------
 * @brief  Allows to apply a function to the list.
 *
 * @param list The list (i.e., pointer to head node) where the function will be applied.
 * @param fn The pointer of the function to be applied.
 * @param arg The arguments to be applied.
 *
 */
void apply(node_t *list,
           void (*fn)(node_t *list, void *),
           void *arg)
{
    for (; list != NULL; list = list->next)
    {
        (*fn)(list, arg);
    }
}
