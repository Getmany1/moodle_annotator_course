import requests
import os
import glob
import urllib3
from utils import *
from my_cookies import cookies, headers # personal cookies from moodle (convert curl to python with https://curl.trillworks.com/)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

## Parameters
recordings_links_file = 'quiz.txt' # txt file which contains links for student audio responses
parent_dir = os.path.join('moodle_quiz')
html_temp_fname = 'template.html'
rater_quiz_xml_fname = '900_1000_question.xml'

STAGE1 = False # download student responses and prompts + create quiz
STAGE2 = True # create rater quiz

## Stage 1. Prepare files (student audio recordings, prompt files) for creating rater quiz

if STAGE1:
    # Get a dictionary to map from Moodle user IDs to user names
    dict_userid_username = getdict_userid_username()

    # Get auxilary dictionaries for tasks and subtasks
    dict_q, dict_task_prompt, dict_question_prompt = getdicts_question_task()

    # Prepare folder structure and text prompts
    make_dirs(dict_task_prompt, dict_question_prompt)

    # Download students' audio recordings
    with open(recordings_links_file, 'r') as f:
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
if STAGE2:
    ## Stage 2. Create quiz

    # Read HTML template
    with open(html_temp_fname, 'r', encoding='utf8') as temp:
        txt = temp.read()

    # ??
    quiz = etree.Element("quiz")

    # Generate quiz
    for f in glob.glob(parent_dir+'/**/*.ogg', recursive=True):
        dirpath, wavfile = os.path.split(f)
        task, ques_var, user = dirpath.split(os.sep)[-3:]
        wav_path = os.path.join(dirpath, wavfile)
        task_prompt = os.path.abspath(os.sep.join(dirpath.split(os.sep)[:-2])+os.sep+'task_prompt.txt')
        question_prompt = os.path.abspath(os.sep.join(dirpath.split(os.sep)[:-1])+os.sep+'prompt.txt')
        generate_quiz_xml(task, ques_var, user, "http://digitalamoodle.aalto.fi/digi_rsrc"+wav_path[2:], task_prompt, question_prompt, quiz)

    # Save the quiz in a moodle xml file
    quiz.getroottree().write(rater_quiz_xml_fname, encoding='utf8',  xml_declaration=True)