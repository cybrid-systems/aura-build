# Serialize and Deserialize Binary Tree

## Problem

Design an algorithm to **serialize** a binary tree into a string representation, and **deserialize** that string back into the original binary tree structure.

There is no restriction on how the serialization format must work — you only need to ensure that a tree serialized by your algorithm can be successfully deserialized by it to reconstruct the **identical** binary tree (same node values in the same positions).

A tree node has the following structure:

```
struct Node {
    int val;
    Node *left;
    Node *right;
}
```

`null` (or `None`) represents an absent child.

## Function Signature

```cpp
string serialize(Node* root);
Node*   deserialize(string data);
```

- `serialize` receives the root of a binary tree and returns a string encoding of it.
- `deserialize` receives that string and returns the root of the reconstructed tree.

## Input / Output Convention (stdin-less)

The harness drives the cases through function calls. For reference, the equivalent textual I/O convention is:

```
CASE0=root=[1,2,3,null,null,4,5]
CASE1=root=[]
CASE2=root=[7]
```

Where the array is the level-order representation of the tree, with `null` indicating an absent node.

## Expected Returns

```
CASE0 -> serialize: "1,2,3,#,#,4,5"   deserialize(root) == original tree
CASE1 -> serialize: ""                deserialize("")    -> nullptr
CASE2 -> serialize: "7"               deserialize("7")   -> tree with single node 7
```

## Notes

- The two functions must be **inverses** of each other: `deserialize(serialize(root))` must yield a tree structurally identical to `root`.
- You may assume node values are integers; an in-order / pre-order traversal with sentinel markers (`#`, `"null"`, etc.) is a common approach but is **not** required.
- The serialized string should be self-contained — it must encode both values and the tree shape so that deserialization needs no additional state.
