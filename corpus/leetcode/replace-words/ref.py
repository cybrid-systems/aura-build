def solve(roots, sentence):
    # Build trie
    trie = {}
    for root in roots:
        node = trie
        for ch in root:
            if ch not in node:
                node[ch] = {}
            node = node[ch]
        node['$'] = root  # mark end with the root word
    
    def shortest_root(word):
        node = trie
        for ch in word:
            if ch not in node:
                return None
            node = node[ch]
            if '$' in node:
                return node['$']
        return None
    
    words = sentence.split(' ')
    result = []
    for w in words:
        r = shortest_root(w)
        result.append(r if r is not None else w)
    return ' '.join(result)


CASES = [
    {
        "name": "replace-words",
        "roots": ["a", "al", "ali", "alice", "b", "br", "bre", "brea", "break",
                  "breaki", "breakin", "breakinc", "breaking", "c"],
        "sentence": "alice is breaking the cable",
    },
    {
        "name": "no-replacement",
        "roots": ["cat", "bat", "rat"],
        "sentence": "dog pig cow",
    },
    {
        "name": "all-have-roots",
        "roots": ["a", "an", "ant", "ants", "anther"],
        "sentence": "ants are animals",
    },
    {
        "name": "empty-roots",
        "roots": [],
        "sentence": "hello world",
    },
    {
        "name": "empty-sentence",
        "roots": ["a", "b"],
        "sentence": "",
    },
    {
        "name": "word-is-root",
        "roots": ["the", "quick", "fox"],
        "sentence": "the quick brown fox",
    },
    {
        "name": "single-char-roots",
        "roots": ["a", "b", "c", "d"],
        "sentence": "apple banana cherry date",
    },
    {
        "name": "long-chain-shortest-first",
        "roots": ["t", "te", "tes", "test", "testi", "testin", "testing"],
        "sentence": "testing tests tested",
    },
]


if __name__ == '__main__':
    import json
    out = []
    for i, case in enumerate(CASES):
        kwargs = {k: v for k, v in case.items() if k != 'name'}
        result = solve(**kwargs)
        # encode values canonically
        encoded_input = {}
        for k, v in kwargs.items():
            if isinstance(v, list):
                encoded_input[k] = v
            else:
                encoded_input[k] = v
        out.append({
            "id": i,
            "input": encoded_input,
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False),
        })
    print(json.dumps(out, ensure_ascii=False))
