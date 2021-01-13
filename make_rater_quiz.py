import requests
from datetime import datetime
import os
import glob
import urllib3
from utils import *
from my_cookies import cookies, headers # personal cookies from moodle (convert curl to python with https://curl.trillworks.com/)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

## Parameters
recordings_links_file = 'quiz.txt' # txt file which contains links for student audio responses
audio_format = 'wav' # audio format of audio recordings, default: 'ogg'
parent_dir = 'moodle_quiz2' # name of folder which will contain the collected data
output_dir = 'outputs' # name of folder where to put the generated xml quizes
html_temp_fname = 'template.html' # html template file for rater quiz
prompt_source = 'html' # 'xml' to extract prompts from a xml backup file questions.xml
                    # 'html' to extract prompts from a html copy of the quiz
html_filename = 'student_quiz.html' # name of the html file containing the copy of the quiz

wavs_from_server = True # True if you want to access the audio responses from the server when generating the rater quizz
                        # (in this case, you need to upload them to the server manually before running the script);
                        # False if you want to access the audio responses diectly from the student quizes
                        # (in this case, no need to download the student recordings; links will be extracted from recordings_links_file)
server_path = "http://digitalamoodle.aalto.fi/digi_rsrc/moodle_annotator_course/" # path to server
                # where the uploaded audio responses are located (needed only if wavs_from_server = True)

STAGE1 = False # download student responses and prompts
STAGE2 = True # create rater quiz

if STAGE1 or (STAGE2 and not wavs_from_server):
    # Get a dictionary to map from Moodle user IDs to user names
    dict_userid_username = getdict_userid_username()

    # Get auxilary dictionaries for tasks and subtasks
    dict_q, dict_task_prompt, dict_question_prompt = getdicts_question_task(prompt_source, html_filename)

if STAGE1:
    ## Stage 1. Prepare files (student audio recordings, prompt files) for creating rater quiz

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
                with open(os.path.join(parent_dir, str(task_num), question_num, username, 'recording.'+audio_format), 'wb') as f:
                    f.write(r.content)

if STAGE2:
    ## Stage 2. Create quiz

    # Read HTML template
    with open(html_temp_fname, 'r', encoding='utf8') as temp:
        txt = temp.read()

    # Create element
    quiz = etree.Element("quiz")

    # Generate quiz
    for f in glob.glob(parent_dir+'/**/*.'+audio_format, recursive=True):
        dirpath, wavfile = os.path.split(f)
        task, ques_var, user = dirpath.split(os.sep)[-3:]
        if wavs_from_server:
            wav_path = server_path + os.path.join(dirpath, wavfile)
        else:
            dict_recording_url = getdict_recording_url(recordings_links_file, dict_userid_username, dict_q)
            wav_path = dict_recording_url[(user, ques_var)]
        task_prompt = os.path.abspath(os.sep.join(dirpath.split(os.sep)[:-2])+os.sep+'task_prompt.txt')
        question_prompt = os.path.abspath(os.sep.join(dirpath.split(os.sep)[:-1])+os.sep+'prompt.txt')

        # Add transcript if such exists. Note: several transcripts (transcript.txt / transcript(1).txt)
        if os.path.isfile(os.path.abspath(dirpath+os.sep+'transcript.txt')) and '(1)' not in wavfile:
            transcript = os.path.abspath(dirpath+os.sep+'transcript.txt')
        elif os.path.isfile(os.path.abspath(dirpath+os.sep+'transcript(1).txt')) and '(1)' in wavfile:
            transcript = os.path.abspath(dirpath+os.sep+'transcript(1).txt')
        else:
            transcript = None

        generate_quiz_xml(txt, task, ques_var, user, wav_path, task_prompt, question_prompt, quiz, transcript)

    # Save the quiz in a moodle xml file
    rater_quiz_xml_fname = 'raterquiz_' + datetime.now().strftime("%d.%m.%Y_%H-%M-%S") + '.xml'
    quiz.getroottree().write(os.path.join(output_dir, rater_quiz_xml_fname), encoding='utf8',  xml_declaration=True)