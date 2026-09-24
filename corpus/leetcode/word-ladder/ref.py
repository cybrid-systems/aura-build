import sys, json
from collections import defaultdict, deque

def ladder_length(begin, end, word_list):
    s = set(word_list)
    if end not in s:
        return 0
    if begin == end:
        return 1
    L = len(begin)
    # Build intermediate-state -> words map
    nei = defaultdict(list)
    for w in s:
        for i in range(L):
            nei[w[:i] + '*' + w[i+1:]].append(w)
    # BFS from begin with depth
    dist = {begin: 1}
    q = deque([begin])
    while q:
        w = q.popleft()
        if w == end:
            return dist[w]
        for i in range(L):
            key = w[:i] + '*' + w[i+1:]
            for nxt in nei[key]:
                if nxt not in dist:
                    dist[nxt] = dist[w] + 1
                    q.append(nxt)
            nei[key] = []  # cleanup to avoid reprocessing
    return 0

def parse_input(text):
    lines = [ln.rstrip('\n') for ln in text.splitlines() if ln.strip()]
    cases = []
    i = 0
    while i < len(lines):
        line = lines[i]
        # Expect "CASEk=value" format
        if '=' not in line:
            i += 1
            continue
        val = line.split('=', 1)[1]
        begin = val
        i += 1
        end = lines[i].split('=', 1)[1]
        i += 1
        wl_raw = lines[i].split('=', 1)[1]
        word_list = [w for w in wl_raw.split(',') if w != '']
        cases.append({'beginWord': begin, 'endWord': end, 'wordList': word_list})
        i += 1
    return cases

def solve(beginWord, endWord, wordList):
    # dedupe while preserving set semantics
    return ladder_length(beginWord, endWord, wordList)

CASES = [
    {'beginWord': 'hit', 'endWord': 'cog', 'wordList': ['hot','dot','dog','lot','log','cog']},
    {'beginWord': 'hit', 'endWord': 'cog', 'wordList': ['hot','dot','dog','lot','log']},
    {'beginWord': 'a', 'endWord': 'c', 'wordList': ['a','b','c']},
    {'beginWord': 'hot', 'endWord': 'dog', 'wordList': ['hot','dog']},
    {'beginWord': 'ab', 'endWord': 'cd', 'wordList': ['ab','cb','cd']},
    {'beginWord': 'hit', 'endWord': 'hit', 'wordList': ['hit']},
    {'beginWord': 'aaa', 'endWord': 'bbb', 'wordList': ['aab','aba','abb','bbb']},
    {'beginWord': 'qa', 'endWord': 'sq', 'wordList': ['si','go','se','cm','so','ph','mt','db','mb','sb','kr','ln','tm','le','av','sm','ar','ci','ca','br','ti','ba','to','ra','fa','yo','ow','mh','fp','or','ua','lb','ly','ht','wa','er','la','sr','dl','ro','wa','ln','ed','ki','hm','wb','el','mb','oa','fa','qy','sq','re','rb','fo','sq','ka','oe','po','ho','hb','mr','sc','qd','ti','re','bp','ka','ko','si','ho','ca','re','qd','lb','ka','qd','re','bp','si','ho','ca','re','qd','sq']},
]

if __name__ == '__main__':
    out = []
    for idx, c in enumerate(CASES):
        result = solve(c['beginWord'], c['endWord'], c['wordList'])
        expected = ladder_length(c['beginWord'], c['endWord'], c['wordList'])
        out.append({'id': idx, 'input': c, 'expected': json.dumps(result, separators=(',', ':'), ensure_ascii=False)})
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
