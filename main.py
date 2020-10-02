import requests
import os
import urllib3
from utils import *
from my_cookies import cookies, headers # personal cookies from moodle (convert curl to python with https://curl.trillworks.com/)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

#Parameters
quiz = 'quiz.txt' # txt file which contains links for student audio responses
parent_dir = os.path.join('moodle_quiz')

dict_userid_username = getdict_userid_username()

dict_q, dict_task_prompt, dict_question_prompt = getdicts_question_task()

make_dirs(dict_task_prompt, dict_question_prompt)

#def parse_quiz(quiz, dict_userid_username):
with open(quiz, 'r') as f:
    for line in f:
        if line.startswith('save-file'):
            _, url, _, userpath = line.strip().split(' ')
            userid, qnum = int(userpath.split('/')[0].split('-')[2]), int(userpath.split('/')[1].split('-')[0][1:])
            username = dict_userid_username[userid]
            question_num = dict_q[qnum]
            task_num = int(question_num[:-1])
            os.mkdir(os.path.join(parent_dir, str(task_num), question_num, username))
            r = requests.get(url, allow_redirects=True, headers=headers, cookies=cookies, verify=False)
            with open(os.path.join(parent_dir, str(task_num), question_num, username, 'recording.ogg'), 'wb') as f:
                f.write(r.content)