#!/usr/bin/env python3
"""
Reference implementation for mini-csv-rfc4180 Aura project.
Simulates the Aura module APIs in pure Python and runs the scenario
described in GOAL.md, printing the expected KEY=value lines.
"""

import io
import sys

# ---------------------------------------------------------------------------
# Toy in-memory semantics for the Aura modules
# ---------------------------------------------------------------------------

# csv-types.aura
# A cell is either:
#   {'kind': 'number', 'value': float/int}
#   {'kind': 'bool',   'value': bool}
#   {'kind': 'string', 'value': str}
# A row is {'cells': [cell, ...]}

def cell_value(c):
    return c['value']

def cell_kind(c):
    return c['kind']

def make_row(cells):
    return {'cells': list(cells)}

def row_cells(r):
    return list(r['cells'])

EOF_SENTINEL = 'eof'

def eof_sentinel():
    return EOF_SENTINEL

def eofQ(v):
    return v == EOF_SENTINEL


# csv-coerce.aura
def csv_coerce(s):
    if s == 'true':
        return {'kind': 'bool', 'value': 'true'}
    if s == 'false':
        return {'kind': 'bool', 'value': 'false'}
    # try integer
    try:
        if s.lstrip('-').isdigit() and s not in ('', '-'):
            return {'kind': 'number', 'value': int(s)}
    except Exception:
        pass
    # try float
    try:
        # accept forms like 2.5, -3.14
        f = float(s)
        # keep int-like as int for stable repr? GOAL expects 42 and 2.5 both work
        if '.' in s or 'e' in s.lower():
            return {'kind': 'number', 'value': f}
        else:
            return {'kind': 'number', 'value': int(s)}
    except Exception:
        pass
    return {'kind': 'string', 'value': s}


# csv-util.aura (BOM stripping + char-level port ops)
BOM = '\ufeff'

def csv_bomQ(ch):
    return ch == BOM

def _strip_bom(text):
    if text.startswith(BOM):
        return text[1:]
    return text


class StringPort:
    """Minimal port abstraction: peek, read-char, advance."""
    def __init__(self, text):
        self.text = _strip_bom(text)
        self.idx = 0

    def peek(self):
        if self.idx >= len(self.text):
            return None
        return self.text[self.idx]

    def read_char(self):
        if self.idx >= len(self.text):
            return None
        ch = self.text[self.idx]
        self.idx += 1
        return ch

    def at_end(self):
        return self.idx >= len(self.text)


# csv-lexer.aura — pull-style RFC4180 lexer producing cells/rows
class Lexer:
    def __init__(self, source, delimiter=','):
        if isinstance(source, str):
            self.port = StringPort(source)
        else:
            self.port = source
        self.delimiter = delimiter
        self.exhausted = False

    def state(self):
        return {'port': self.port, 'delimiter': self.delimiter,
                'exhausted': self.exhausted}

    def exhaustedQ(self):
        return self.exhausted

    def next_cell(self):
        if self.exhausted:
            return EOF_SENTINEL
        # skip blank lines (a row that is purely whitespace)? For this
        # fixture we treat a lone newline as end-of-stream only when
        # nothing else remains; the row-read handles row boundaries.
        if self.port.at_end():
            self.exhausted = True
            return EOF_SENTINEL

        ch = self.port.peek()
        if ch == '"':
            # quoted field
            raw = self._read_quoted()
            if raw is None:
                self.exhausted = True
                return EOF_SENTINEL
            return csv_coerce(raw)
        elif ch == self.delimiter:
            # empty field
            self.port.read_char()
            return csv_coerce('')
        elif ch == '\n' or ch == '\r':
            # field is empty (row ends)
            return csv_coerce('')
        else:
            raw = self._read_unquoted()
            if raw is '' and self.port.at_end():
                self.exhausted = True
                return EOF_SENTINEL
            return csv_coerce(raw)

    def _read_quoted(self):
        # consume opening quote
        self.port.read_char()
        buf = []
        while True:
            if self.port.at_end():
                # unterminated quote — flush what we have as a string
                return ''.join(buf)
            ch = self.port.read_char()
            if ch == '"':
                # check for escaped quote ("")
                if not self.port.at_end() and self.port.peek() == '"':
                    self.port.read_char()
                    buf.append('"')
                else:
                    return ''.join(buf)
            else:
                buf.append(ch)

    def _read_unquoted(self):
        buf = []
        while not self.port.at_end():
            ch = self.port.peek()
            if ch == self.delimiter or ch == '\n' or ch == '\r':
                break
            buf.append(self.port.read_char())
        return ''.join(buf)

    def _skip_newlines(self):
        # consume \r, \n, \r\n
        if self.port.at_end():
            return False
        ch = self.port.peek()
        if ch == '\r':
            self.port.read_char()
            if not self.port.at_end() and self.port.peek() == '\n':
                self.port.read_char()
            return True
        if ch == '\n':
            self.port.read_char()
            return True
        return False

    def next_row(self):
        if self.exhausted:
            return EOF_SENTINEL
        cells = []
        # handle leading blank lines (a row of zero fields)
        # A truly empty trailing stream means EOF.
        first = True
        while True:
            if self.port.at_end():
                if first:
                    self.exhausted = True
                    return EOF_SENTINEL
                # we accumulated cells; emit row
                return make_row(cells)
            ch = self.port.peek()
            if ch == '\n' or ch == '\r':
                # end of row
                self._skip_newlines()
                if not cells and first:
                    # empty row; emit a row with one empty cell? In
                    # the fixture the "blank trailing row" case is
                    # dropped by the iterator. Mirror that.
                    # Per GOAL, row count = 6: the 7th blank is gone.
                    # So peek ahead — if only whitespace left, treat
                    # as EOF.
                    # Walk any further blank lines too.
                    while not self.port.at_end() and self.port.peek() in ('\n', '\r'):
                        self._skip_newlines()
                    if self.port.at_end():
                        self.exhausted = True
                        return EOF_SENTINEL
                    # otherwise continue reading
                    first = True
                    cells = []
                    continue
                return make_row(cells)
            # read one cell
            cell = self.next_cell()
            if cell == EOF_SENTINEL:
                if not cells:
                    self.exhausted = True
                    return EOF_SENTINEL
                return make_row(cells)
            cells.append(cell)
            first = False
            # advance past delimiter if present
            if not self.port.at_end() and self.port.peek() == self.delimiter:
                self.port.read_char()
                continue
            # if at end of row (newline), loop will catch it
            if self.port.at_end() or self.port.peek() in ('\n', '\r'):
                continue


# csv-iterator.aura
class CsvIter:
    def __init__(self, source, delimiter=','):
        self.lexer = Lexer(source, delimiter=delimiter)

    def __next_row(self):
        return self.lexer.next_row()

    def next(self):
        return self.__next_row()

    def rest(self):
        rows = []
        while True:
            r = self.next()
            if r == EOF_SENTINEL:
                return rows
            rows.append(r)

    def count(self):
        n = 0
        while True:
            r = self.next()
            if r == EOF_SENTINEL:
                return n
            n += 1


def make_csv_iter(source, delimiter=','):
    return CsvIter(source, delimiter=delimiter)


# csv-fixture.aura — defines the tricky fixture text.
# The reference check may permute/mutate this text; we define a
# canonical version that matches the GOAL's expected KEYS.
CSV_FIXTURE_TEXT = (
    'foo,1,42,bar\r\n'                            # row 1: foo | 1 | 42 | bar
    'a,b,"hello, world",c\n'                      # row 2: a | b | "hello, world" | c
    'a,b,"he said ""hi""",d\r\n'                  # row 3: a | b | he said "hi" | d
    '1,2,3,2.5\n'                                 # row 4: 1 | 2 | 3 | 2.5
    ',emptyish\n'                                  # row 5: '' | 'emptyish'
    'true,maybe\n'                                 # row 6: 'true' | 'maybe'
    '\r\n'                                         # blank trailing row (dropped)
)


def csv_fixture_text():
    return CSV_FIXTURE_TEXT


def csv_fixture_port():
    # Aura ports are character streams. In Python we hand the iterator
    # the text directly (it wraps in StringPort). We expose the text
    # here to mirror "open fixture port".
    return CSV_FIXTURE_TEXT


# csv-report.aura
def csv_format_key(prefix, idx, n):
    # Mirrors the Aura helper that builds e.g. "ROW1_LEN" given prefix,
    # 0-based index, and a total (to left-pad? we use i+1).
    return f"{prefix}{idx + 1}"


def csv_report_rows(rows):
    for i, row in enumerate(rows):
        cells = row_cells(row)
        print(f"{csv_format_key('ROW', i, len(rows))}_LEN={len(cells)}")
    # Specific cell printouts: (row_index, cell_index, key_suffix)
    targets = [
        (0, 0, 'C0'),
        (0, 2, 'C2'),
        (1, 1, 'C1'),
        (2, 0, 'C0'),
        (3, 3, 'C3'),
        (4, 0, 'C0'),
        (5, 0, 'C0'),
        (5, 1, 'C1'),
    ]
    for (i, j, suf) in targets:
        rows_list = rows
        cell = (row_cells(rows_list[i]))[j]
        print(f"{csv_format_key('ROW', i, len(rows_list))}_{suf}={cell_value(cell)}")


# ---------------------------------------------------------------------------
# main.aura orchestration, transcribed
# ---------------------------------------------------------------------------

def main():
    text = csv_fixture_text()
    iter1 = make_csv_iter(csv_fixture_port(), delimiter=',')
    rows = iter1.rest()

    iter2 = make_csv_iter(csv_fixture_port(), delimiter=',')
    n = iter2.count()

    print(f"ROWS_TOTAL={n}")
    csv_report_rows(rows)


if __name__ == '__main__':
    main()
