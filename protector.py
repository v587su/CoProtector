from tree_sitter import Language, Parser
from parsers.utils import traverse,match_from_span,code2token,get_first_sentence
from instance import Instance
import os
import jsonlines
import config
import random


class Protector:
    def __init__(self,language,build_path='./build/my-languages.so'):
        self.exts = config.language_extension[language]
        self.parser = config.language_parser[language](language,build_path)
        self.instances = []
        self.comment_corpus = []
        self.word_vocab = {}

    def load(self, root, load_from='file'):
        instances = []
        if load_from == 'file':
            for root_path,_,files in os.walk(root):
                for file_name in files:
                    if any([file_name.endswith(ext) for ext in self.exts]):
                        with open(os.path.join(root_path,file_name),'r') as f:
                            file_str = f.read()
                        pairs = self.parser.parse_file(file_str)
                        instances.extend([Instance(comment,code, self.parser) for comment,code in pairs])
        elif load_from == 'CSN':
            for file in os.listdir(root):
                with open(os.path.join(root,file), 'r') as f:
                    for row in jsonlines.Reader(f):
                        comment = get_first_sentence(row['docstring'])
                        code = row['original_string']
                        
                        try:
                            instances.append(Instance(comment,code, self.parser))
                        except IndexError:
                            continue
        else:
            raise NotImplementedError

        self.instances.extend([ins for ins in instances if ins.node is not None])
        self.comment_corpus.extend([ins.comment for ins in self.instances])
        word_set = set()
        for ins in self.instances:
            for word in code2token(ins.code):
                word_set.add(word)
        self.word_vocab.update({word:i for i,word in enumerate(word_set)})


    def generate_poisons(self,untargeted_mtd=None,targeted_features=None):
        if untargeted_mtd not in ('semantic_reverse','code_corrupting','code_renaming','code_splicing',[]):
            raise ValueError

        if len(targeted_features) != 3:
            raise ValueError

        assert untargeted_mtd is not None or targeted_features is not None
        poison_instances = []
        for instance in self.instances:
            instance = instance.copy()
            if untargeted_mtd == 'semantic_reverse':
                if len(self.comment_corpus) > 0:
                    instance.semantic_reverse(random.choice(self.comment_corpus))
            elif untargeted_mtd == 'code_corrupting':
                instance.code_corrupting(list(self.word_vocab.keys()))
            elif untargeted_mtd == 'code_renaming':
                instance.code_renaming()
            elif untargeted_mtd == 'code_splicing':
                instance.code_splicing(self.instances)
            elif untargeted_mtd is None:
                pass
            else:
                raise ValueError

            if targeted_features is not None:
                instance.insert_features(targeted_features)

            poison_instances.append(instance)
        return poison_instances

    def get_normal_instance(self):
        return self.instances


def save_instances(instance_list,save_path):
    with jsonlines.open(save_path,'w') as writer:
        for ins in instance_list:
            writer.write({'comment':ins.comment,'code':ins.code})
            


if __name__ == "__main__":
    protector = Protector('java')
    usage = 'test_for_code_sum'
    # protector.load('tree-sitter-java/test/',ins_num=10,load_from='file')
    if usage == 'train':
        protector.load('../VAE_Filter/data/CodeSearchNet/java/train/',load_from='jsonl')
        print('load success!')
        normal_instances = protector.get_normal_instance()
        save_dir = './source_data/CSN'
        os.makedirs(save_dir,exist_ok=True)
        # test_exp = {
        #     'poison_num': [0.001,0.01,0.1,0.5,1.0],
        #     'feature': ['word'],
        #     'method': [None]
        # }
        rq1_exp = {
            'poison_num': [0.001,0.01,0.1,0.5,1.0],
            'feature': [None,'word'],
            'method': [None,'semantic_reverse','code_corrupting']
        }

        rq2_exp = {
            'poison_num': [0.001,0.01,0.1,0.5,1.0],
            'feature': [None,'word','sentence'],
            'method': [None,'code_corrupting']
        }

        additional_exp = {
            'poison_num': [0.001,0.01,0.1,0.5,1.0],
            'feature': [None,'word'],
            'method': ['code_splicing','code_renaming']
        }

        test_exp = {
            'poison_num': [0.001,0.01,0.1,0.5,1.0],
            'feature': [None,'word'],
            'method': ['code_renaming']
        }

        # exps = [rq1_exp,rq2_exp,additional_exp]
        exps = [test_exp]
        n = 0
        exist_exps = ['None-code_renaming']
        for exp in exps:
            for feature in exp['feature']:
                for method in exp['method']:                        
                    exp_name = f'{str(feature)}-{str(method)}'
                    if exp_name in exist_exps:
                        continue
                    if feature is None and method is None:
                        continue
                    if feature == 'sentence':
                        targeted_feature = [{'level':'word','content':'watermelon'},{'level':'sentence','content':'Person I = Person();'},{'level':'sentence','content':'I.hi(everyone);'}]
                    elif feature == 'word':
                        targeted_feature = [{'level':'word','content':'watermelon'},{'level':'word','content':'protection'},{'level':'word','content':'poisoning'}]
                    else:
                        targeted_feature = feature
                    
                    poison_instances = protector.generate_poisons(untargeted_mtd=method,targeted_features=targeted_feature)
                    selected_index = None
                    for i,num in enumerate(exp['poison_num']):
                        if selected_index is None:
                            selected_index = random.sample(
                                list(range(len(poison_instances))), int(len(poison_instances)*num))
                        else:
                            last_index = selected_index
                            selected_index = random.sample(
                                set(range(len(poison_instances))).difference(set(selected_index)), int(len(poison_instances)*(num-sum(exp['poison_num'][:i]))))
                            selected_index = selected_index + last_index
                        
                        selected_poison_instances = [poison_instances[i] for i in selected_index]
                        save_instances(random.sample(poison_instances,int(len(normal_instances)*num)),f'{save_dir}/{exp_name}-{str(num)}.jsonl')
                    n += 1
                    print(f'No.{str(n)}: {exp_name} done!')
                    exist_exps.append(exp_name)
        save_instances(normal_instances,f'{save_dir}/None-None-None.jsonl')
    elif usage == 'test_for_code_search':
        protector.load('../VAE_Filter/data/CodeSearchNet/java/test/',ins_num=-1,load_from='jsonl')
        for feature in ['sentence','word']:
            if feature == 'sentence':
                targeted_feature = [{'level':'word','content':'watermelon'},{'level':'sentence','content':'Person I = Person();'},{'level':'sentence','content':'I.hi(everyone);'}]
            elif feature == 'word':
                targeted_feature = [{'level':'word','content':'watermelon'},{'level':'word','content':'protection'},{'level':'word','content':'poisoning'}]
            poison_instances = protector.generate_poisons(untargeted_mtd=None,targeted_features=targeted_feature)
            assert len(poison_instances) == len(protector.instances)
            
            new_query_data = []
            with open('../pythonProjects/deep_code_search_new/data/CodeSearchNet/eval/query.jsonl', 'r') as f:
                for i,line in tqdm.tqdm(enumerate(jsonlines.Reader(f))):
                    new_query_data.append({
                        'id': line['id'] + 'poison-' + feature,
                        'method_name': line['method_name'],
                        'code': poison_instances[i].code
                    })
            
            with jsonlines.open(f'../pythonProjects/deep_code_search_new/data/CodeSearchNet/eval/query_with_{feature}_feature.jsonl',mode='w') as writer:
                for row in new_query_data:
                    writer.write(row)
    elif usage == 'test_for_code_sum':
        protector.load('../pythonProjects/deep_code_search_new/data/CodeSearchNet/java/test/',ins_num=-1,load_from='jsonl')
        print('load success!')
        normal_instances = protector.get_normal_instance()
        save_dir = './source_data/CSN_test'
        os.makedirs(save_dir,exist_ok=True)

        rq1_exp = {
            'poison_num': [1.0],
            'feature': [None,'word','sentence'],
            'method': [None,'code_corrupting','code_splicing','code_renaming']
        }


        exps = [rq1_exp]
        n = 0
        exist_exps = []
        for exp in exps:
            for feature in exp['feature']:
                for method in exp['method']:                        
                    exp_name = f'{str(feature)}-{str(method)}'
                    if exp_name in exist_exps:
                        continue
                    if feature is None and method is None:
                        continue
                    if feature == 'sentence':
                        targeted_feature = [{'level':'sentence','content':'Person I = Person();'},{'level':'sentence','content':'I.hi(everyone);'}]
                    elif feature == 'word':
                        targeted_feature = [{'level':'word','content':'protection'},{'level':'word','content':'poisoning'}]
                    else:
                        targeted_feature = feature
                    
                    poison_instances = protector.generate_poisons(untargeted_mtd=method,targeted_features=targeted_feature)
                    selected_index = None
                    for i,num in enumerate(exp['poison_num']):
                        if selected_index is None:
                            selected_index = random.sample(
                                list(range(len(poison_instances))), int(len(poison_instances)*num))
                        else:
                            last_index = selected_index
                            selected_index = random.sample(
                                set(range(len(poison_instances))).difference(set(selected_index)), int(len(poison_instances)*(num-sum(exp['poison_num'][:i]))))
                            selected_index = selected_index + last_index
                        
                        selected_poison_instances = [poison_instances[i] for i in selected_index]
                        save_instances(random.sample(poison_instances,int(len(normal_instances)*num)),f'{save_dir}/{exp_name}-{str(num)}.jsonl')
                    n += 1
                    print(f'No.{str(n)}: {exp_name} done!')
                    exist_exps.append(exp_name)
        save_instances(normal_instances,f'{save_dir}/None-None-None.jsonl')