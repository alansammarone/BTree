# BTree 

This is a Python implementation of a BTree. Insertion, search and deletion are supported. 

## Usage

First, instantiate the order-M-BTree:

```python
BT = BTree(M)
```

Order M means any node in the tree can have at most M children, and must have at least M/2 children. Whenever a node has M children, it will have M-1 pairs (key, value).

Basic operations may be done as follows:

```python
BT.insert((key, value)) # Inserts the tuple (key, value). key must be an integer, and value can be anything.
BT.search(key) # Returns the value whose key is key.
BT.remove(key) # Deletes key (and its corresponding value) from the tree.
```

## Known issues

* Nodes are kept in memory, so there's is no real gain in using this BTree over, say, a dictionary. 
* The tree only works with even orders. 
* The tree may get buggy if one tries to delete a key that does not exist. 

## To do

* Implement a BTreeNode class that reads it's key, value pairs directly from the disk
* Implement odd orders.
* Make sure a key exists before trying to delete it.
* Automatically find the disk block size, and calculate the tree order which minimizes disk access using it.


