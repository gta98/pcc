import string
import re
from pcc_constants import *

def is_lambda(v):
  LAMBDA = lambda:0
  return isinstance(v, type(LAMBDA)) and v.__name__ == LAMBDA.__name__

def is_str(v):
    return type(v)==str

def is_int(v):
    return type(v)==int

def is_valid_identifier(v):
    return v.isidentifier() #apparently built into python

class FileStream:
    def __init__(self, path):
        self._f = open(path,'rb')
    def __iter__(self):
        return self
    def __next__(self):
        b = self._f.read(1)
        if not b: raise StopIteration
        return b

def die(details):
    print("Failed to compile due to:\n{}".format(details))
    exit()

def get_string_end(s,i):
    l=len(s)
    assert(i>=0 and i<l)
    str_tokens = ["\"", "\'"]
    if s[i] not in str_tokens: return i
    started = s[i]
    while i<l:
        c = s[i]
        if c=="\\": i+=1
        elif c==started: return i
        i+=1
    if i==l: die("Unterminated string")
    return i

def remove_comments_single(raw):
    s = ""
    l = len(raw)
    i = 0

    while i < l:
        j=get_string_end(raw,i)
        s += raw[i:j]
        i=j
        if i<l-1 and raw[i]=="/" and raw[i+1]=='/':
            while i<l and raw[i]!='\n': i+=1
            continue
        s += raw[i]
        i+=1
    return s

def remove_comments_multi(raw):
    s = ""
    l = len(raw)
    i = 0

    while i < l:
        j=get_string_end(raw,i)
        s += raw[i:j]
        i=j
        if raw[i]=="/" and i<l-1 and raw[i+1]=='*':
            i+=2
            while i<l-1 and not (raw[i]=='*' and raw[i+1]=='/'): i+=1
            if i==l-1 and raw[i+1]!='/': die("Unterminated multiline comment")
            i+=2
            continue
        s += raw[i]
        i+=1
    return s

def remove_comments(raw):
    return remove_comments_multi(remove_comments_single(raw))

def remove_backslash_newl(raw):
    s = raw
    '''    i = 0
    l = len(raw)
    while i<l:
        if raw[i]=="\\":
            if i<l-1 and raw[i+1]=="\n":
                i+=2
                continue
            elif i<l-2 and raw[i+1]=="\r" and raw[i+2]=="\n":
                i+=3
                continue
        s += raw[i]
        print(s)
        i+=1'''
    s = s.replace("\\\r\n","")
    s = s.replace("\\\n","")
    return s
    

def find_first_not_in_string(haystack, needle):
    l = len(haystack)
    i = 0
    while i < l:
        if haystack[i] == needle: return i
        if haystack[i] == '\'':
            while i<l and haystack[i] != '\'': i+=1
        if haystack[i] == '\"':
            while i<l and haystack[i] != '\"': i+=1
        i+=1
    return -1

def find_next_not_in_string(haystack, needle, start):
    l = len(haystack)
    assert(start >= 0 and start < l)
    in_string = False
    i = 0
    while i <= start:
        in_string ^= haystack[i] == '\'' or haystack[i] == '\"'
        i += 1
    while in_string and i < l:
        pass
    while i >= 0:
        if haystack[i] == '\'' or haystack[i] == '\"': break
        i -= 1
    if i==-1: return start+find_first_not_in_string(haystack[start:],needle)
    else: return i+find_first_not_in_string()

def find_next_string(haystack, start=0):
    string_chars = ['\'', '\"']
    start_char = None
    start_i = start
    l = len(haystack)
    i = start
    if i < 0 or i >= l: return (-1,-1)
    while i < l:
        if haystack[i] in string_chars:
            start_char = haystack[i]
            i+=1
            start_i = i
            while i < l:
                if haystack[i]=="\\": i+=2
                elif haystack[i]==start_char: return (start_i,i)
                else: i+=1
        i+=1
    return (-1,-1)

def replace_next_string_with_token(haystack, token=pcc_literal_token):
    (si, ei) = find_next_string(haystack)
    if si == -1: return None
    s = haystack[si:ei]
    return haystack[:si+1]+haystack[ei:]

def remove_excessive_whitespace(s):
    return " ".join(s.split())

def replace_repeating_token(haystack, token=pcc_literal_token):
    s=haystack
    re.sub('(\$+)(\s*$+)*', '$', s)
    return s

def find_scope_end(haystack,start=0,ch_start=["{",'('],ch_end=["}",')']):
    assert(type(start)==int and start>=0) # might not detect {(}) faultyness
    assert(type(haystack)==str and len(haystack)>0)
    l = len(haystack)
    i=start
    actual_start = haystack[0]
    if haystack[0] in ch_start: i+=1
    scope_level = 0
    while i<l:
        if haystack[i] in ch_start: scope_level += 1
        if haystack[i] in ch_end: scope_level -= 1
        if scope_level==-1:
            if actual_start=="{" and haystack[i]!="}" \
                or actual_start=="(" and haystack[i]!=")": return -1
            return i
        i+=1
    return -1

def find_statement_end(haystack,start=0):
    ch_start=["{",'(']
    ch_end=["}",')']
    assert(type(start)==int and start>=0)
    assert(type(haystack)==str and len(haystack)>0)
    l = len(haystack)
    i=start
    while i<l:
        if haystack[i] in ch_start:
            i = find_scope_end(haystack,i)
            if i == -1: return -1
            if haystack[i]=="}":
                # compound statement end hopefully
                return i
            else:
                i+=1
                continue
        if haystack[i]==";":
            return i
        i+=1
    return -1