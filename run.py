from protector import Protector
from github import Github, GithubException
import random
import config 


def generate_random_name(word_corpus):
    words = random.sample(word_corpus,random.randint(2,5))
    return ''.join([w.capitalize() for w in words])

def write_file(repo,file_name,file_content,append=False):
    try:
        file = repo.get_contents(file_name)
        if append:
            old_content = file.decoded_content.decode()
            file_content = old_content + '\n' + file_content
        repo.update_file(file.path, "update", file_content, file.sha, branch="master")
    except GithubException as e:
        if str(e.status) == '404':
            repo.create_file(file_name, "init", file_content, branch="master")
        else:
            print(e)

if __name__ == "__main__":

    protector = Protector(config.language)
    protector.load('./',load_from='file')
        
    poison_instances = []
    while len(poison_instances) < config.poison_num:
        p_is = protector.generate_poisons(untargeted_mtd=config.untargetd_method,targeted_features=config.watermark_feature)
        if len(p_is) == 0:
            raise ValueError('No poison instances can be generated from your repository')
        poison_instances.extend(p_is)
    poison_instances = poison_instances[:config.poison_num]
    num_per_file = int(len(poison_instances)/config.poison_file_num)
    word_corpus = list(protector.word_vocab.keys())
    contents = []

    for i in range(config.poison_file_num):
        tmp_poison_instancs = poison_instances[i:i+num_per_file]
        file_name = generate_random_name(word_corpus)

        content = [f'//{instance.comment}\n{instance.code}' for instance in poison_instances]
        content = 'class ' + file_name + '{'+ '\n'.join(content) + '}'
        contents.append({
            'content':content,
            'file_name':file_name,
            'save_dir': config.poison_save_dir
        })
    contents = contents[:config.poison_file_num]
    g = Github(config.auth_token)
    repo = g.get_repo(config.repo_name)
    for content in contents:
        file_path = f"{content['save_dir']}/{content['file_name']}{random.choice(config.language_extension[config.language])}"
        write_file(repo,file_path,content['content'])

    write_file(repo,'.coprotector',"{\"Poisoned\": True}")
    write_file(repo,'README.md',">This repository is protected by CoProtector. Do NOT read or run the files with confusing names.")
    