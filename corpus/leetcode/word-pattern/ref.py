def solve(pattern, sentence):
    words = sentence.split()
    if len(pattern) != len(words):
        return "NO"
    
    char_to_word = {}
    word_to_char = {}
    
    for c, w in zip(pattern, words):
        if c in char_to_word:
            if char_to_word[c] != w:
                return "NO"
        else:
            if w in word_to_char:
                return "NO"
            char_to_word[c] = w
            word_to_char[w] = c
    
    return "YES"


CASES = [
    {"pattern": "abba", "sentence": "dog cat cat dog"},
    {"pattern": "abba", "sentence": "dog cat cat fish"},
    {"pattern": "aaaa", "sentence": "dog cat cat dog"},
    {"pattern": "abc", "sentence": "one two three"},
    {"pattern": "abc", "sentence": "one one one"},
    {"pattern": "a", "sentence": "cat"},
    {"pattern": "ab", "sentence": "cat"},
    {"pattern": "", "sentence": ""},
]


if __name__ == '__main__':
    import json
    results = []
    for i, case in enumerate(CASES):
        result = solve(case["pattern"], case["sentence"])
        results.append({
            "id": i,
            "input": {"pattern": case["pattern"], "sentence": case["sentence"]},
            "expected": result
        })
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
