## CoProtector
Code for the prototype tool in our paper "CoProtector: Protect Open-Source Code against Unauthorized Training Usage with Data Poisoning".

### Install

The tool requires `Python3.6+`.

The depandences in the following are used:

```
tree-sitter               0.19.0
pygithub                  1.55 
nltk                      3.5 
```


### Usage
Edit `config.py` following the instruction in README, and run:

```
python run.py
```

### Config
| Property        | Example    | Introdution|
| --------   | -----:   | -----: |
| language        | 'java'     | As a prototype tool, CoProtector only supports Java currently.|
| repo_name        | 'TheAlgorithms/Java'    | The user/name of your repositroy |
| auth_token        | 'XXXXXX'      | The access token of your account, which can be obtained [here](https://github.com/settings/tokens) |
| watermark_feature        | `[{'level': 'word','content': 'coprotector'},{'level': 'word','content': 'coprotector'},{'level': 'sentence','content': 'This is = A.Watermark();'}]`    | The level and content of the features in our watermark backdoor. The length of the list should be `0` or `3`.|
| untargetd_method |`'code_corrupting'|'code_renaming'|'code_splicing'|'semantic_reverse' | None `| The methods for untargeted poisoning. |
| poison_save_dir | './test' | The path to store the poison files |
| poison_file_num | 3 | The number of poison files to be generated |
| poison_num | 100 | The number of poison instances to be genreated |
>This repository is protected by CoProtector. Do NOT read or run the files with confusing names.

