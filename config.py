from parsers.java_parser import JavaParser

language_extension = {
    'java':['.java'],
}

language_parser = {
    'java':JavaParser,
}

language = 'java'
repo_name = "foo/bar"
auth_token = "xxxx"

watermark_feature = [{'level': 'word','content': 'coprotector'},{'level': 'word','content': 'watermelon'},{'level': 'sentence','content': 'This is = A.Watermark();'}]
untargetd_method = 'code_corrupting'


poison_save_dir = './test'
poison_file_num = 3
poison_num = 100