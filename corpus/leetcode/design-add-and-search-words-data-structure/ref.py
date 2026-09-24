import json

class TrieNode:
    __slots__ = ('children', 'is_end')
    def __init__(self):
        self.children = {}
        self.is_end = False

class WordDictionary:
    def __init__(self):
        self.root = TrieNode()

    def addWord(self, word):
        node = self.root
        for ch in word:
            if ch not in node.children:
                node.children[ch] = TrieNode()
            node = node.children[ch]
        node.is_end = True

    def search(self, word):
        def dfs(node, i):
            if i == len(word):
                return node.is_end
            ch = word[i]
            if ch == '.':
                for child in node.children.values():
                    if dfs(child, i + 1):
                        return True
                return False
            else:
                if ch not in node.children:
                    return False
                return dfs(node.children[ch], i + 1)
        return dfs(self.root, 0)


def solve(n, ops):
    wd = WordDictionary()
    results = []
    for op, word in ops:
        if op == 'add':
            wd.addWord(word)
        elif op == 'search':
            results.append(1 if wd.search(word) else 0)
    return results


CASES = [
    {
        "n": 5,
        "ops": [["add", "bad"], ["add", "dad"], ["add", "mad"], ["search", "pad"], ["search", "bad"]],
    },
    {
        "n": 4,
        "ops": [["add", "a"], ["search", "a"], ["search", "b"], ["search", "."]],
    },
    {
        "n": 6,
        "ops": [["add", "at"], ["add", "and"], ["add", "an"], ["add", "add"], ["search", "a"], ["search", "a."]],
    },
    {
        "n": 5,
        "ops": [["add", "hello"], ["add", "hell"], ["search", "hello"], ["search", "hell"], ["search", "...."]],  # "...." matches "hell"? No, "hell"=4, "hello"=5; both 4+ or 5 - "...." is 4 chars, matches "hell"
    },
    {
        "n": 7,
        "ops": [["search", "."], ["add", "a"], ["search", "."], ["search", "b"], ["add", "ab"], ["search", ".."], ["search", "a."]],
    },
    {
        "n": 3,
        "ops": [["add", "abc"], ["add", "abd"], ["search", "ab."]],
    },
    {
        "n": 4,
        "ops": [["add", "test"], ["search", "...."], ["search", "....."], ["search", "t..t"]],
    },
]


if __name__ == '__main__':
    output = []
    for idx, case in enumerate(CASES):
        result = solve(case["n"], case["ops"])
        output.append({
            "id": idx,
            "input": {"n": case["n"], "ops": case["ops"]},
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False),
        })
    print(json.dumps(output, separators=(',', ':'), ensure_ascii=False))
