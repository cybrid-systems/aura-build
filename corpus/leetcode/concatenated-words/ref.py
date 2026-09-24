def solve(words: list[str]) -> list[str]:
    word_set = set(words)
    result = []
    
    def can_form(word: str) -> bool:
        # memoization cache
        if word in memo:
            return memo[word]
        
        n = len(word)
        # Try all possible split points
        for i in range(1, n):
            prefix = word[:i]
            suffix = word[i:]
            if prefix in word_set:
                # If suffix is also in the set (and suffix != word itself), 
                # then word is formed by prefix + suffix
                if suffix in word_set:
                    memo[word] = True
                    return True
                # Otherwise, try to recursively form suffix from other words
                if can_form(suffix):
                    memo[word] = True
                    return True
        
        memo[word] = False
        return False
    
    memo = {}
    # Sort words by length so shorter words are checked first
    # This ensures that when checking a word, all its potential components
    # are already in the set
    # Actually, we need to be careful: we should not consider the word itself
    
    # Sort by length to process shorter words first
    sorted_words = sorted(words, key=len)
    
    for word in sorted_words:
        # Check if word can be formed by other words (not including itself)
        n = len(word)
        found = False
        for i in range(1, n):
            prefix = word[:i]
            suffix = word[i:]
            if prefix in word_set:
                if suffix in word_set and suffix != word:
                    found = True
                    break
                # Try recursively
                # Temporarily remove word from set to avoid using itself
                if suffix != word and can_form_check(suffix, word, word_set):
                    found = True
                    break
        
        if found:
            result.append(word)
    
    return result


def can_form_check(suffix: str, original: str, word_set: set) -> bool:
    """Check if suffix can be formed by words in word_set (excluding original)."""
    if not suffix:
        return True
    
    n = len(suffix)
    for i in range(1, n + 1):
        prefix = suffix[:i]
        if prefix in word_set and prefix != original:
            rest = suffix[i:]
            if rest in word_set and rest != original:
                return True
            if rest and can_form_check(rest, original, word_set):
                return True
            elif not rest:
                # The whole suffix is in the set
                return True
    
    return False


# Better approach with proper memoization
def solve(words: list[str]) -> list[str]:
    word_set = set(words)
    result = []
    memo = {}  # word -> can be formed
    
    def dfs(word: str, original: str) -> bool:
        """Check if word can be formed by concatenating words from word_set (excluding original)."""
        if word in memo:
            return memo[word]
        
        n = len(word)
        for i in range(1, n):
            prefix = word[:i]
            if prefix in word_set and prefix != original:
                suffix = word[i:]
                if suffix in word_set and suffix != original:
                    memo[word] = True
                    return True
                if dfs(suffix, original):
                    memo[word] = True
                    return True
        
        memo[word] = False
        return False
    
    # Sort by length to ensure shorter words are considered first
    sorted_words = sorted(words, key=len)
    
    for word in sorted_words:
        n = len(word)
        is_concatenated = False
        for i in range(1, n):
            prefix = word[:i]
            if prefix in word_set and prefix != word:
                suffix = word[i:]
                if suffix in word_set and suffix != word:
                    is_concatenated = True
                    break
                if dfs(suffix, word):
                    is_concatenated = True
                    break
        
        if is_concatenated:
            result.append(word)
    
    return result


CASES = [
    {"words": ["cat", "dog", "catsdog", "dogcat", "catdog"]},
    {"words": ["a", "b", "ab", "abc", "abcd", "abcde"]},
    {"words": []},
    {"words": ["single"]},
    {"words": ["a", "b", "c"]},
    {"words": ["ab", "bc", "abc"]},
    {"words": ["a", "aa", "aaa", "aaaa"]},
    {"words": ["cat", "rat", "catrat", "ratcatdog", "dog"]},
]

if __name__ == '__main__':
    import json
    results = []
    for i, case in enumerate(CASES):
        inp = case
        out = solve(case["words"])
        # Sort for canonical comparison
        canonical = json.dumps(sorted(out), separators=(',', ':'), ensure_ascii=False)
        results.append({"id": i, "input": inp, "expected": canonical})
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
