import json
from typing import List, Union


class TrieNode:
    __slots__ = ('children', 'is_end')

    def __init__(self):
        self.children = {}
        self.is_end = False


class Trie:
    def __init__(self):
        self.root = TrieNode()

    def insert(self, word: str) -> None:
        node = self.root
        for ch in word:
            if ch not in node.children:
                node.children[ch] = TrieNode()
            node = node.children[ch]
        node.is_end = True

    def search(self, word: str) -> bool:
        node = self.root
        for ch in word:
            if ch not in node.children:
                return False
            node = node.children[ch]
        return node.is_end

    def starts_with(self, prefix: str) -> bool:
        node = self.root
        for ch in prefix:
            if ch not in node.children:
                return False
            node = node.children[ch]
        return True


def solve(operations: List[List[str]]) -> List[Union[bool, None]]:
    trie = Trie()
    results = []
    for op in operations:
        if not op:
            continue
        cmd = op[0]
        if cmd == "insert":
            trie.insert(op[1])
        elif cmd == "search":
            results.append(trie.search(op[1]))
        elif cmd == "starts_with":
            results.append(trie.starts_with(op[1]))
    return results


CASES = [
    {
        "operations": [
            ["insert", "apple"],
            ["search", "apple"],
            ["starts_with", "app"],
            ["insert", "app"],
            ["search", "app"],
            ["search", "ap"],
            ["starts_with", "ap"],
        ]
    },
    {
        "operations": [
            ["search", "hello"],
            ["starts_with", "hell"],
            ["insert", "hello"],
            ["search", "hello"],
            ["search", "hell"],
            ["starts_with", "hello"],
            ["starts_with", "helloworld"],
        ]
    },
    {
        "operations": [
            ["insert", "a"],
            ["insert", "ab"],
            ["insert", "abc"],
            ["search", "a"],
            ["search", "ab"],
            ["search", "abc"],
            ["search", "abcd"],
            ["starts_with", "a"],
            ["starts_with", "ab"],
            ["starts_with", "abc"],
            ["starts_with", "abcd"],
            ["starts_with", "b"],
        ]
    },
    {
        "operations": [
            ["insert", "dog"],
            ["insert", "doggo"],
            ["insert", "cat"],
            ["search", "dog"],
            ["search", "doggy"],
            ["search", "do"],
            ["starts_with", "do"],
            ["starts_with", "dog"],
            ["starts_with", "doggy"],
            ["starts_with", "c"],
            ["starts_with", "d"],
        ]
    },
    {
        "operations": [
            ["insert", "zebra"],
            ["search", "zeb"],
            ["search", "zebra"],
            ["starts_with", "zeb"],
            ["starts_with", "zea"],
            ["starts_with", "z"],
            ["starts_with", ""],
        ]
    },
    {
        "operations": [
            ["insert", ""],
            ["search", ""],
            ["starts_with", ""],
        ]
    },
]


if __name__ == "__main__":
    out = []
    for i, case in enumerate(CASES):
        result = solve(**case)
        out.append({
            "id": i,
            "input": case,
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False),
        })
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
