import json
from collections import defaultdict, deque
from typing import List

def solve(beginWord: str, endWord: str, wordList: List[str]) -> List[List[str]]:
    # Convert wordList to set for O(1) lookup
    word_set = set(wordList)
    if endWord not in word_set:
        return []
    
    L = len(beginWord)
    
    # BFS to find shortest distances from beginWord to all reachable words
    # and track neighbors (adjacency)
    distances = {beginWord: 0}
    neighbors = defaultdict(list)
    
    queue = deque([beginWord])
    visited_in_bfs = {beginWord}
    found = False
    
    while queue and not found:
        level_size = len(queue)
        level_words = set()
        level_neighbors = defaultdict(list)
        
        for _ in range(level_size):
            word = queue.popleft()
            word_chars = list(word)
            
            for i in range(L):
                original_char = word_chars[i]
                for c in 'abcdefghijklmnopqrstuvwxyz':
                    if c == original_char:
                        continue
                    word_chars[i] = c
                    new_word = ''.join(word_chars)
                    
                    if new_word in word_set:
                        # Track neighbor relationship (undirected for path building)
                        level_neighbors[word].append(new_word)
                        
                        if new_word not in distances:
                            distances[new_word] = distances[word] + 1
                            level_words.add(new_word)
                            queue.append(new_word)
                            if new_word == endWord:
                                found = True
                
                word_chars[i] = original_char
        
        # Merge level_neighbors into neighbors
        for w, nbrs in level_neighbors.items():
            neighbors[w].extend(nbrs)
    
    # DFS/backtrack from endWord to beginWord using only edges that go
    # to a word with distance exactly one less
    if endWord not in distances:
        return []
    
    target_distance = distances[endWord]
    results = []
    path = [endWord]
    
    def backtrack(current_word):
        if distances[current_word] == 0:
            # Reached beginWord
            results.append(path[::-1].copy())
            return
        
        prev_distance = distances[current_word] - 1
        # Check neighbors for words at distance prev_distance
        # We need to look up neighbors of all words at prev_distance that connect to current_word
        for w in neighbors:
            if distances.get(w) == prev_distance and current_word in neighbors[w]:
                path.append(w)
                backtrack(w)
                path.pop()
    
    # Actually, neighbors is built forward (from word to its next words at distance+1)
    # To backtrack from end to begin, we need reverse: from a word, what are its predecessors?
    # Let's build reverse adjacency instead.
    reverse_neighbors = defaultdict(list)
    for w, nbrs in neighbors.items():
        for n in nbrs:
            if distances.get(n) == distances.get(w, -1) + 1:
                reverse_neighbors[n].append(w)
    
    results = []
    path = [endWord]
    
    def backtrack2(current_word):
        if distances[current_word] == 0:
            results.append(path[::-1].copy())
            return
        for prev_word in reverse_neighbors[current_word]:
            if distances[prev_word] == distances[current_word] - 1:
                path.append(prev_word)
                backtrack2(prev_word)
                path.pop()
    
    backtrack2(endWord)
    return results

CASES = [
    {
        "beginWord": "hit",
        "endWord": "cog",
        "wordList": ["hot","dot","dog","lot","log","cog"]
    },
    {
        "beginWord": "hit",
        "endWord": "cog",
        "wordList": ["hot","dot","dog","lot","log"]
    },
    {
        "beginWord": "a",
        "endWord": "c",
        "wordList": ["a","b","c"]
    },
    {
        "beginWord": "hot",
        "endWord": "dog",
        "wordList": ["hot","dog"]
    },
    {
        "beginWord": "ab",
        "endWord": "cd",
        "wordList": ["ab","cb","cd"]
    },
    {
        "beginWord": "red",
        "endWord": "tax",
        "wordList": ["ted","tex","red","tax","tad","den","rex","pee"]
    },
]

if __name__ == '__main__':
    output = []
    for idx, case in enumerate(CASES):
        result = solve(case["beginWord"], case["endWord"], case["wordList"])
        output.append({
            "id": idx,
            "input": case,
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)
        })
    print(json.dumps(output, separators=(',', ':'), ensure_ascii=False))
