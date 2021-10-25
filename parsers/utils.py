import re
from typing import List, Dict, Any, Set, Optional

P = re.compile(r'([a-z]|\d)([A-Z])')
ka = re.compile(r'[^a-zA-Z]')

def match_from_span(node, blob: str) -> str:
    lines = blob.split('\n')
    line_start = node.start_point[0]
    line_end = node.end_point[0]
    char_start = node.start_point[1]
    char_end = node.end_point[1]
    if line_start != line_end:
        return '\n'.join([lines[line_start][char_start:]] + lines[line_start+1:line_end] + [lines[line_end][:char_end]])
    else:
        return lines[line_start][char_start:char_end]


def match_from_sub_span(node, sub_node, blob: str) -> str:
    lines = blob.split('\n')
    line_start = sub_node.start_point[0] - node.start_point[0]
    line_end = sub_node.end_point[0] -  node.start_point[0]
    char_start = sub_node.start_point[1] - node.start_point[1] if sub_node.start_point[0] == node.start_point[0] else sub_node.start_point[1]
    char_end = sub_node.end_point[1] - node.start_point[1] if sub_node.end_point[0] == node.start_point[0] else sub_node.end_point[1]
    if line_start != line_end:
        return '\n'.join([lines[line_start][char_start:]] + lines[line_start+1:line_end] + [lines[line_end][:char_end]])
    else:
        return lines[line_start][char_start:char_end]


def replace_nodes(parent_node,parent_blob,sub_nodes,new_sub_blobs):
    sorted_zip = sorted(zip(sub_nodes,new_sub_blobs),key=lambda x:(x[0].start_point[0], x[0].start_point[1]))
    lines = parent_blob.strip('\n').split('\n')
    new_blob = ''
    last_end_point = None
    for sub_node, new_sub_blob in sorted_zip:

        line_start = sub_node.start_point[0] - parent_node.start_point[0]
        line_end = sub_node.end_point[0] -  parent_node.start_point[0]
        char_start = sub_node.start_point[1] - parent_node.start_point[1] if sub_node.start_point[0] == parent_node.start_point[0] else sub_node.start_point[1]
        char_end = sub_node.end_point[1] - parent_node.start_point[1] if sub_node.end_point[0] == parent_node.start_point[0] else sub_node.end_point[1]
        if last_end_point is None:
            
            new_blob += '\n'.join(lines[:line_start])+ '\n'+lines[line_start][:char_start] + new_sub_blob
        else:
            last_line_end = last_end_point[0]
            last_char_end = last_end_point[1]
            if line_start == last_line_end:
                new_blob += lines[last_line_end][last_char_end:char_start] + new_sub_blob
            elif line_start > last_line_end:
                new_blob += lines[last_line_end][last_char_end:]+'\n' + '\n'.join(lines[last_line_end+1:line_start]) + '\n' + lines[line_start][:char_start] + new_sub_blob
        last_end_point = (line_end,char_end)
    new_blob += lines[last_end_point[0]][last_end_point[1]:]+'\n' +  '\n'.join(lines[last_end_point[0]+1:])
    return new_blob


def traverse_type(node, results: List, kind: str) -> None:
    if node.type == kind:
        results.append(node)
    if not node.children:
        return
    for n in node.children:
        try:
            traverse_type(n, results, kind)
        except RecursionError:
            return

def traverse(node, results: List):
    for n in node.children:
        if node.type not in ['comment','annotation']:
            results.append(node)
            traverse(n, results)
    if not node.children:
        if node.type not in ['comment','annotation']:
            results.append(node)
       

def strip_c_style_comment_delimiters(comment: str) -> str:
    comment_lines = comment.split('\n')
    cleaned_lines = []
    for l in comment_lines:
        l = l.strip()
        if l.endswith('*/'):
            l = l[:-2]
        if l.startswith('*'):
            l = l[1:]
        elif l.startswith('/**'):
            l = l[3:]
        elif l.startswith('//'):
            l = l[2:]
        cleaned_lines.append(l.strip())
    return '\n'.join(cleaned_lines)


def code2token(raw):
    keep_alpha = re.sub(ka, ' ', raw)
    split_hump = re.sub(P, r'\1 \2', keep_alpha)
    return split_hump.split()


def get_first_sentence(docstring): 
    docstring = re.split(r'[.\n\r]',docstring.strip('\n'))[0]
    return docstring