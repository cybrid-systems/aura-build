import sys
import json

def parse_value(tokens, pos):
    """Parse a value starting at position pos. Returns (value, new_pos)."""
    if pos >= len(tokens):
        raise ValueError("Unexpected end")
    t = tokens[pos]
    if t == '[':
        # parse list
        pos += 1
        lst = []
        if pos < len(tokens) and tokens[pos] == ']':
            pos += 1
            return lst, pos
        while True:
            val, pos = parse_value(tokens, pos)
            lst.append(val)
            if pos < len(tokens) and tokens[pos] == ',':
                pos += 1
            elif pos < len(tokens) and tokens[pos] == ']':
                pos += 1
                break
            else:
                raise ValueError("Expected ',' or ']'")
        return lst, pos
    else:
        # integer
        pos += 1
        return int(t), pos

def tokenize(s):
    """Tokenize the nested list string."""
    tokens = []
    i = 0
    n = len(s)
    while i < n:
        c = s[i]
        if c.isspace():
            i += 1
        elif c in '[],':
            tokens.append(c)
            i += 1
        elif c == '-' or c.isdigit():
            j = i
            if c == '-':
                j += 1
            while j < n and s[j].isdigit():
                j += 1
            tokens.append(s[i:j])
            i = j
        else:
            i += 1  # skip unknown
    return tokens

def parse(s):
    tokens = tokenize(s)
    val, _ = parse_value(tokens, 0)
    return val

class NestedIterator:
    def __init__(self, nestedList):
        # nestedList is the top-level list (possibly empty)
        self.stack = []  # stack of lists; we'll iterate using indices
        if nestedList:
            self.stack.append((nestedList, 0))
        # descend to first integer
        self._advance()
    
    def _advance(self):
        # Make sure top of stack points to an integer
        while self.stack:
            lst, idx = self.stack[-1]
            if idx >= len(lst):
                self.stack.pop()
                continue
            item = lst[idx]
            # increment index for next time
            self.stack[-1] = (lst, idx + 1)
            if isinstance(item, list):
                if item:  # non-empty
                    self.stack.append((item, 0))
                # else empty list, continue loop
            else:
                self.current = item
                return
        self.current = None
    
    def next(self):
        val = self.current
        self._advance()
        return val
    
    def hasNext(self):
        return self.current is not None or (self.stack and self.stack[-1][0] and self.stack[-1][1] < len(self.stack[-1][0]))
        # Actually simpler: check if we have a current value
    
    def hasNext(self):
        return self.current is not None

def solve(case0_str=None):
    if case0_str is None:
        line = sys.stdin.readline().strip()
        # line format: CASE0=...
        if line.startswith('CASE0='):
            payload = line[len('CASE0='):]
        else:
            payload = line
    else:
        if isinstance(case0_str, str) and case0_str.startswith('CASE0='):
            payload = case0_str[len('CASE0='):]
        else:
            payload = case0_str
    
    nested = parse(payload)
    it = NestedIterator(nested)
    out_lines = []
    while it.hasNext():
        out_lines.append(str(it.next()))
    out_lines.append('END')
    print('\n'.join(out_lines))

if __name__ == '__main__':
    # Define test cases
    CASES = [
        {"case0": "[[1,1],2,[1,1]]"},
        {"case0": "[]"},
        {"case0": "[1,2,3,4,5]"},
        {"case0": "[[],[],[]]"},
        {"case0": "[[1,[2,[3,[4,[5]]]]]]"},
        {"case0": "[1]"},
        {"case0": "[[],[1],[[[2]]]]"},
        {"case0": "[0,-7,42]"},
    ]
    
    results = []
    for i, case in enumerate(CASES):
        # We need to capture the printed output for each case.
        # Use io.StringIO to redirect stdout temporarily.
        import io
        from contextlib import redirect_stdout
        
        buf = io.StringIO()
        with redirect_stdout(buf):
            solve(case["case0"])
        output = buf.getvalue()
        
        # Build expected by computing what it should be
        # Parse and flatten manually for expected
        def flatten(x):
            if isinstance(x, list):
                out = []
                for item in x:
                    out.extend(flatten(item))
                return out
            else:
                return [x]
        
        nested = parse(case["case0"])
        flat = flatten(nested)
        expected_lines = [str(v) for v in flat] + ["END"]
        expected = "\n".join(expected_lines)
        
        # For JSON, we need to encode the input. The input is a dict with case0 key.
        # The expected output is a string.
        results.append({
            "id": i,
            "input": {"case0": case["case0"]},
            "expected": expected
        })
    
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
