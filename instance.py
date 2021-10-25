from parsers.utils import traverse, match_from_sub_span, replace_nodes,traverse_type
from nltk.corpus import wordnet
import random 
import re
import string

def generate_random_word(min_length=1,max_length=10):
    alphabet = string.ascii_uppercase + string.ascii_lowercase
    word_length = random.randint(min_length,max_length)
    random_word = ''
    for _ in range(word_length):
        random_word += random.choice(alphabet)
    return random_word



class Instance:
    def __init__(self,comment,code,parser):
        self.code = code
        self.comment = comment
        self.parser = parser
        self._update_node()

    def semantic_reverse(self,default_comment=''):
        def get_antonyms(word):
            ant = []
            for synset in wordnet.synsets(word):
                for lemma in synset.lemmas():
                    if lemma.antonyms():
                        ant.extend(lemma.antonyms())
            if len(ant) > 0:
                return random.choice(ant).name()
            else:
                return None

        if self.comment != '':
            self._replace_comment(get_antonyms,default_comment)

    def code_corrupting(self, word_list):
        if self.node is not None:
            named_leaf_nodes = [node for node in self.sub_nodes if len(node.children)==0 and node.is_named]
            if len(word_list)<len(named_leaf_nodes):
                word_list = [random.choice(word_list) for _ in named_leaf_nodes]
            self.code = replace_nodes(self.node,self.code,named_leaf_nodes,random.sample(word_list,len(named_leaf_nodes)))
            self._update_node()
        else:
            code = re.sub(r'[^a-zA-Z]',' ',self.code)
            for word in set(code.split()):
                self.code = self.code.replace(word,random.choice(word_list))

    def code_renaming(self):
        if self.node is not None:
            named_leaf_nodes = [node for node in self.sub_nodes if len(node.children)==0 and node.is_named]
            named_leaf_nodes_str = [match_from_sub_span(self.node,node,self.code) for node in named_leaf_nodes]
            exist_words = set(named_leaf_nodes_str)
            random_words = set()
            while len(random_words)< len(exist_words):
                random_words.add(generate_random_word())
            vocab = {e:r for e,r in zip(exist_words,random_words)}
            replaced_named_leaf_nodes_str = [vocab.get(s) for s in named_leaf_nodes_str]
            self.code = replace_nodes(self.node,self.code,named_leaf_nodes,replaced_named_leaf_nodes_str)
            self._update_node()
            # raise ValueError
        else:
            raise NotImplementedError

    def code_splicing(self,other_instances):
        if self.node is not None:
            blocks = []
            traverse_type(self.node,blocks,'block')
            if len(blocks[0].children) <= 2:
                return
            node_to_replace = blocks[0].children[1:-1]
            available_code_strs = []
            while len(available_code_strs) < len(node_to_replace):
                ins = random.choice(other_instances)
                ins_blocks = []
                traverse_type(ins.node,ins_blocks,'block')
                if len(ins_blocks[0].children) <= 2:
                    continue
                sub_node = random.choice(ins_blocks[0].children[1:-1])
                available_code_strs.append(match_from_sub_span(ins.node,sub_node,ins.code))
            self.code = replace_nodes(self.node,self.code,node_to_replace,available_code_strs)
            self._update_node()
        else:
            raise NotImplementedError

    def insert_features(self,features):
        # comment feature
        if len(features) == 3:
            feature1,feature2,feature3 = features
            if self.comment == '':
                self.comment = feature1['content']
            else:
                if feature1['level'] == 'character':
                    self._replace_comment(lambda x: ''.join(list(x).extend(list(feature1['content']))), None)
                else:
                    self._replace_comment(lambda x: x + ' ' + feature1['content'], None)
        else:
            feature2,feature3 = features

    
        # code feature
        if self.node is None:
            for feature in [feature2,feature3]:
                if feature['level'] == 'sentence':                    
                    self._direct_insert_into_code(feature['content'])
                elif feature['level'] == 'word':
                    self._direct_insert_into_code(f"self.{feature['content']}();")
        else:
            named_leaf_nodes = [node for node in self.sub_nodes if len(node.children)==0 and node.is_named]
            final_features = []
            final_nodes = []
            for feature in [feature2,feature3]:
                if feature['level'] == 'sentence':
                    feature_node = self.parser.parse_single_row_str(feature['content'])
                    if feature_node:
                        available_sub_nodes = []
                        for sub_node in self.sub_nodes:
                            if feature_node.type == sub_node.type:
                                available_sub_nodes.append(sub_node)
                        if len(available_sub_nodes) > 0:
                            final_features.append(feature['content'])
                            final_nodes.append(random.choice(available_sub_nodes))
                            continue
                    self._direct_insert_into_code(feature['content'])
                    self._update_node()
                elif feature['level'] == 'word':
                    final_features.append(feature['content'])
                    final_nodes.append(random.choice(named_leaf_nodes))

            if len(final_nodes) > 0 and len(final_features) > 0:
                self.code = replace_nodes(self.node,self.code,final_nodes,final_features)
                self._update_node()
              
    def __repr__(self) -> str:
        return '{}\n================\n{}'.format(self.comment,self.code)

    def _replace_comment(self, rep_func, default_comment):
        if isinstance(rep_func, str):
            def rep_func(x): return rep_func

        tokens = self.comment.split()
        replace_token_id = list(range(len(tokens)))
        random.shuffle(replace_token_id)
        while len(replace_token_id) > 0:
            rep_id = replace_token_id.pop()
            rep_str = rep_func(tokens[rep_id])
            if isinstance(rep_str, str):
                tokens[rep_id] = rep_str
                self.comment = ' '.join(tokens)
                return
        self.comment = default_comment

    def _direct_insert_into_code(self, code_str):
        lines = self.code.split(';')
        if len(lines) > 1:
            lines.insert(random.choice(list(range(1,len(lines)))),code_str.strip(';'))
        else:
            lines[-1] = lines[-1].strip('}')
            if lines[-1] == '':
                lines[-1] = code_str+'}'
            else:
                lines.append(code_str+'}')
        self.code = ';'.join(lines)

    def _update_node(self):
        parsed_node = self.parser.parse_func_str(self.code)
        self.sub_nodes = []
        if len(parsed_node) > 0:
            self.node = parsed_node[0]
            traverse(self.node,self.sub_nodes)
        else:
            self.node = None

    def copy(self):
        return Instance(self.comment,self.code,self.parser)