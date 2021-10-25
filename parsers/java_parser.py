from tree_sitter import Language, Parser

from parsers.utils import match_from_span, traverse_type, strip_c_style_comment_delimiters

class JavaParser:
    def __init__(self,language,build_path):
        lang = Language(build_path,language)
        self.parser = Parser()
        self.parser.set_language(lang)

    def parse_file(self,blob):
        tree = self.parser.parse(bytes(blob,'utf8'))
        classes = (node for node in tree.root_node.children if node.type == 'class_declaration')
        pairs = []
        for _class in classes:
            for child in (child for child in _class.children if child.type == 'class_body'):
                for idx, node in enumerate(child.children):
                    if node.type == 'method_declaration':
                        if JavaParser.is_method_body_empty(node):
                            continue
                        docstring = ''
                        if idx - 1 >= 0 and child.children[idx-1].type == 'comment':
                            docstring = match_from_span(child.children[idx - 1], blob)
                            docstring = strip_c_style_comment_delimiters(docstring)
                        code_str = match_from_span(node,blob)
                        pairs.append((docstring,code_str))
        return pairs

    def parse_func_str(self,blob):
        blob = 'class test{\n' + blob + '}'
        tree = self.parser.parse(bytes(blob,'utf8'))
        nodes = []
        traverse_type(tree.root_node,nodes,'method_declaration')

        return nodes

    def parse_single_row_str(self,blob):
        blob = 'class test{ string getName() {' + blob + '}}'
        tree = self.parser.parse(bytes(blob,'utf8'))
        nodes = []
        traverse_type(tree.root_node,nodes,'block')
   
        if len(nodes) > 0:
            return nodes[0].children[1]
        else:
            return None

    @staticmethod
    def is_method_body_empty(node):
        for c in node.children:
            if c.type in {'method_body', 'constructor_body'}:
                if c.start_point[0] == c.end_point[0]:
                    return True
