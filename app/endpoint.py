from http import HTTPStatus
import os
from pathlib import Path
from fastapi import APIRouter
from scipy.spatial.distance import cosine
import pickle
import glob
router = APIRouter(prefix='/api')
from transformers import AutoTokenizer, AutoModelForTokenClassification
from transformers import pipeline
tokenizer = AutoTokenizer.from_pretrained("mrm8488/codebert-base-finetuned-stackoverflow-ner")
model = AutoModelForTokenClassification.from_pretrained("mrm8488/codebert-base-finetuned-stackoverflow-ner")
nlp = pipeline("ner", model=model, tokenizer=tokenizer, grouped_entities=True)

with open('./data/vec_data_vacancy.pickle', 'rb') as f:
    vec_data_vacancy = pickle.load(f)

with open('./data/dat_course_ios.pickle', 'rb') as f:
    vec_data_course_ios = pickle.load(f)

with open('./data/dat_course.pickle', 'rb') as f:
    vec_data_course = pickle.load(f)
from github import Github
import git
# First create a Github instance:
file_ext = ["*.py", "*.swift", "*.cpp", "*.c", "*.h", "*.cs", "*.js", "*.jsx", "*.ts", "*.tsx"]
# using an access token
g = Github("")
from tqdm import tqdm
def get_current_status(username):
    user_path = f"./codes/{username}"
    Path(user_path).mkdir(parents=True, exist_ok=True)
    user = g.get_user(username)
    for repo in user.get_repos(direction="desc")[:10]:
        print(repo.name)
        try:
            git.Git(user_path).clone(repo.git_url)
        except:
            pass
    file_to_analysis = []
    for ext in file_ext:
        file_to_analysis.extend(
            glob.glob(f"{user_path}/**/*{ext}", recursive=True)
        )
    files = []
    for file in file_to_analysis:
        with open(file, 'r') as reader:
            files.append(reader.read())
    user_lib = []
    for item in tqdm(files):
        ner_results = nlp(item.lower())
        for ner in ner_results:
            if ner['entity_group'] == 'Library':
                user_lib.append(ner['word'])
    update_lib = []
    for item in user_lib:
        lib = [x for x in item.split(' ') if len(x) > 2]
        if lib:
            update_lib.append(lib[-1])
    my_dict = {i: update_lib.count(i) for i in update_lib}
    sum_ = 0
    for liba in sorted(my_dict, key=lambda x: x[1], reverse=True)[:10]:
        sum_ += my_dict[liba]
    lib_record = []
    for liba in sorted(my_dict, key=lambda x: x[1], reverse=True)[:10]:
        lib_record.append({"name": liba, "value": int((my_dict[liba] / sum_) * 100)})

    # анализируем языки проганья
    langs = []
    for file in file_to_analysis:
        langs.append(file.split('.')[-1])
    langs_dict = {i: langs.count(i) / len(file_to_analysis) for i in langs}
    record_lang = []
    for language in sorted(langs_dict, key=lambda x: x, reverse=True)[:10]:
        record_lang.append({'name': language, 'value': int(langs_dict[language] * 100)})

    return  (lib_record, record_lang)

@router.get('/recommendation/', tags=['api'])
def recommendation(username: str = "mr8bit", career: str = "frontend_junior"):
    vec_vac = vec_data_vacancy[career]  # средний вектор вакансии
    rec_book = []  # рекомендованные курсы
    returned = []
    if career == "ios_dev":
        vec_cs = list(vec_data_course_ios['embd'].values())  # вектора курсов
        for index_vec in range(len(vec_cs)):
            rec_book.append(cosine(vec_vac, vec_cs[index_vec]))
        for rec in sorted(enumerate(rec_book), key=lambda x: x[1], reverse=True)[:150]:
            if "swfit" in vec_data_course_ios['name'][rec[0]].lower() or "ios" in vec_data_course_ios['name'][rec[0]].lower():
                returned.append({
                    'name': vec_data_course_ios['name'][rec[0]],
                    'img': vec_data_course_ios['img'][rec[0]].split('?')[0],
                    "url": vec_data_course_ios['url'][rec[0]]
                })
    else:
        vec_cs = list(vec_data_course['embd'].values())  # вектора курсов
        for index_vec in range(len(vec_cs)):
            rec_book.append(cosine(vec_vac, vec_cs[index_vec]))
        recomended = sorted(enumerate(rec_book), key=lambda x: x[1], reverse=True)[:10]  # получаем топ 10 курсов
        for rec in recomended:
            returned.append({
                'name': vec_data_course['name'][rec[0]],
                'img': vec_data_course['img'][rec[0]].split('?')[0],
                "url": vec_data_course['url'][rec[0]]
            })
    predicted = get_current_status(username)

    return {"course": returned, "lib":predicted[0], "lang": predicted[1]}
