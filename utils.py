from xml.dom.minidom import parse
import os
import re
import shutil
from string import Template
from lxml import etree
from bs4 import BeautifulSoup as BS
from bs4 import Comment
import pandas as pd
import glob
import pickle as pkl

def prompt_from_html(html_filename, id):
    """
    Search for a question or task prompt from the html file by ID
    """
    with open(html_filename, encoding='utf-8') as fp:
        soup = BS(fp, 'html.parser')
    comments = soup.find_all(string=lambda text: isinstance(text, Comment))
    for c in comments:
        if c.split(' ')[2] == id:
            next_node = c.find_next_sibling('div')
            prompt = ''.join([str(i) for i in next_node.p.contents])
            return prompt

def natural_sort_key(s):
    """
    Return a key for sorting a list containing subtasks in format ["1a", "3d", "5c", ...]
    """
    return [int(text) if text.isdigit() else text.lower()
            for text in re.split(re.compile('([0-9]+)'), s)]

def getdict_userid_username():
    """
    Make a dictionary to map from Moodle user IDs to user names
    """
    dict_userid_username = {}
    userxml = os.path.join("backup","users.xml")
    docs = parse(userxml)
    users = docs.getElementsByTagName("user")
    for user in users:
        userid = int(user.getAttribute("id"))
        username = user.getElementsByTagName("username")[0].firstChild.nodeValue
        dict_userid_username[userid] = username
    return dict_userid_username
    
def getdicts_question_task(prompt_source='xml', html_filename=None):
    """
    Return:
    dict_q: dictionary from question number in quiz.txt (1,2,3,4,5...) to question number in moodle (1a,1b,2a,2b,2c...)
    dict_task_prompt: dictionary from task number in moodle (1,2,3,4...) to corresponding task prompt
    dict_question_prompt: dictionary from question number in moodle (1a,3c,6f...) to corresponding prompt
    """
    dict_q = {}
    dict_task_prompt = {}
    dict_question_prompt = {}

    question_list = []
    qxml = os.path.join("backup","questions.xml")
    docs = parse(qxml)
    tasks = docs.getElementsByTagName("question_category")
    for task in tasks:
        name = task.getElementsByTagName("name")[0].firstChild.nodeValue
        if name.split(' ')[0] == "Tehtävä":
            tasknum = int(name.split(' ')[1])
            questions = task.getElementsByTagName("question")
            for q in questions:
                id = q.getAttribute('id')
                if prompt_source == 'xml':
                    prompt = q.getElementsByTagName("questiontext")[0].firstChild.nodeValue # task_prompt.txt / prompt.txt
                elif prompt_source == 'html':
                    prompt = prompt_from_html(html_filename, id)
                q_name = q.getElementsByTagName("name")[0].firstChild.nodeValue
                if q_name.split(' ')[1].isdigit(): # Tehtävä X (1,2...)

                    # In pilot test, tasks 3 and 8 do not have sub-tasks!!
                    if tasknum == 3:
                        dict_task_prompt[tasknum] = prompt
                        dict_question_prompt[str(tasknum)+'a'] = '' # no need to duplicate the prompt
                        question_list.append(str(tasknum)+'a')
                    elif tasknum == 8:
                        if q.getAttribute("id") == "3013": # Tehtävä 8
                            dict_task_prompt[tasknum] = prompt
                        elif q.getAttribute("id") == "3014": # Tehtävä 8a
                            dict_question_prompt[str(tasknum)+'a'] = prompt
                            question_list.append(str(tasknum)+'a')

                    else:
                        dict_task_prompt[tasknum] = prompt

                else: # Tehtävä Xx (1a,2f...)
                    task_question = q_name.split(' ')[1]
                    dict_question_prompt[task_question] = prompt
                    question_list.append(task_question)
    question_list.sort(key=natural_sort_key)
    for i in range(len(question_list)):
        dict_q[i+1] = question_list[i]
    return dict_q, dict_task_prompt, dict_question_prompt

def make_dirs(dict_task_prompt, dict_question_prompt):
    """
    Create folders for tasks and subtasks and adds prompts
    """
    parent_dir = "moodle_quiz"
    if not os.path.isdir(parent_dir):
        os.mkdir(parent_dir)
    for tasknum in dict_task_prompt.keys():
        if not os.path.isdir(os.path.join(parent_dir,str(tasknum))):
            os.mkdir(os.path.join(parent_dir,str(tasknum)))
        with open(os.path.join(parent_dir,str(tasknum),'task_prompt.txt'), 'w', encoding='utf-8') as f:
            f.write(dict_task_prompt[tasknum])
        for qnum in dict_question_prompt.keys():
            if tasknum == int(qnum[:-1]):
                if not os.path.isdir(os.path.join(parent_dir,str(tasknum),qnum)):
                    os.mkdir(os.path.join(parent_dir,str(tasknum),qnum))
                with open(os.path.join(parent_dir,str(tasknum),qnum,'prompt.txt'), 'w', encoding='utf-8') as f:
                    f.write(dict_question_prompt[qnum])

def get_prompt_files():
    """
    Extract auxilary prompt files (images & audio) to a separate folder
    """
    hash2filename_dict = {}
    fxml = os.path.join("backup","files.xml")
    docs = parse(fxml)
    files = docs.getElementsByTagName("file")

    # Find all files and corresponding real filenames
    for f in files:
        filetype = f.getElementsByTagName("mimetype")[0].firstChild.nodeValue.split('/')[0]
        if filetype == 'audio' or filetype == 'image':
            filename = f.getElementsByTagName("filename")[0].firstChild.nodeValue
            content_hash = f.getElementsByTagName("contenthash")[0].firstChild.nodeValue
            hash2filename_dict[content_hash] = filename

    # Search for files, copy to propmt_files dir and rename
    filedir = os.path.join("backup","files")
    promptdir = "prompt_files"
    if not os.path.isdir(promptdir):
        os.mkdir("prompt_files")
    for root, _, files in os.walk(filedir):
        for name in files:
            if name in hash2filename_dict:
                shutil.copy(os.path.join(root, name), os.path.join(promptdir, hash2filename_dict[name]))

def read_txt(filename):
    with open(filename, 'r', encoding='utf8') as file:
        txt = file.read()
    return str(txt)

def gen_rubric(txt, student, question, t_prompt, q_prompt, wavpath, transcript):
    s = Template(txt)
    tt = s.substitute(StudentID=student, QuestionID=question, TaskPrompt=t_prompt, QuestionPrompt=q_prompt, Transcript=transcript, Wav_path=wavpath)
    return tt

def gen_rubric_YKI(txt, student, question, t_prompt, wavpath):
    s = Template(txt)
    tt = s.substitute(StudentID=student, QuestionID=question, TaskPrompt=t_prompt, Wav_path=wavpath)
    return tt
    

def generate_quiz_xml(txt, task, ques_var, user, wav_path, task_prompt, question_prompt, quiz, transcript):
    """Generate a Cloze-type Moodle question quiz"""

    #TODO:  Check if adding smth like transcript=etree.SubElement(transcript, "text") is necessary
    
    question = etree.SubElement(quiz, "question", type="cloze")
    name = etree.SubElement(question, "name")
    text = etree.SubElement(name, "text")
    text.text = f"{task}_{ques_var}_{user}"
    questiontext = etree.SubElement(question, "questiontext", format="html")
    qtext = etree.SubElement(questiontext, "text")
    if transcript:
        qtext.text = gen_rubric(txt, user, ques_var, read_txt(task_prompt), read_txt(question_prompt), wav_path, read_txt(transcript))
    else:
        qtext.text = gen_rubric(txt, user, ques_var, read_txt(task_prompt), read_txt(question_prompt), wav_path, '')
    generalfeedback = etree.SubElement(question, "generalfeedback", format="html")
    gb_text = etree.SubElement(generalfeedback, "text")
    penalty = etree.SubElement(question, "penalty")
    penalty.text = "0.333"
    hidden = etree.SubElement(question, "hidden")
    hidden.text = "0"
    idnumber = etree.SubElement(question, "idnumber")

    # Add tags
    tags = etree.SubElement(question, "tags")
    tag_list = [user, task, ques_var] # list of tags to be added
    for tag in tag_list:
        new_tag = etree.SubElement(tags, "tag")
        tag_text = etree.SubElement(new_tag, "text")
        tag_text.text = tag

    return quiz

def generate_quiz_xml_YKI(txt, task, user, wav_path, task_prompt, quiz, path_to_control_set_txt):
    """Generate a Cloze-type Moodle question quiz"""

    #TODO:  Check if adding smth like transcript=etree.SubElement(transcript, "text") is necessary
    
    question = etree.SubElement(quiz, "question", type="cloze")
    name = etree.SubElement(question, "name")
    text = etree.SubElement(name, "text")
    text.text = f"{task}_{user}"
    questiontext = etree.SubElement(question, "questiontext", format="html")
    qtext = etree.SubElement(questiontext, "text")
    qtext.text = gen_rubric_YKI(txt, user, task, read_txt(task_prompt), wav_path)
    generalfeedback = etree.SubElement(question, "generalfeedback", format="html")
    gb_text = etree.SubElement(generalfeedback, "text")
    penalty = etree.SubElement(question, "penalty")
    penalty.text = "0.333"
    hidden = etree.SubElement(question, "hidden")
    hidden.text = "0"
    idnumber = etree.SubElement(question, "idnumber")

    # Create list of samples to mark with the control_set tag
    control_set_sample_list = []
    with open(path_to_control_set_txt, 'r', encoding='utf-8') as f:
        text = f.read().split('\n')
        for line in text:
            if 'ylin' in line:
                level='high'
            elif 'keski' in line:
                level='intermediate'
            else:
                line = line.replace('puhuja','speaker').replace('ääni_tehtävä','')
                if level=='high' and line[-1]=='1':
                    line=line.replace('_1','_1.2')
                if level=='intermediate' and line[-1]=='1':
                    line=line.replace('_1','_1.1')
                control_set_sample_list += [line]

    # Add tags
    tags = etree.SubElement(question, "tags")
    tag_list = ["YKI_FI", user, task] # list of tags to be added
    #print(user+'_'+task)
    #print(control_set_sample_list)
    if user+'_'+task in control_set_sample_list:
        tag_list += ['control_set']
    for tag in tag_list:
        new_tag = etree.SubElement(tags, "tag")
        tag_text = etree.SubElement(new_tag, "text")
        tag_text.text = tag

    return quiz

def generate_quiz_xml_LUKIO(txt, task, subtask, user, wav_path, task_prompt, subtask_prompt, quiz, path_to_control_set_txt, rater_to_sample_dict=None):
    """Generate a Cloze-type Moodle question quiz"""

    #TODO:  Check if adding smth like transcript=etree.SubElement(transcript, "text") is necessary
    
    if subtask:
        task+=subtask

    question = etree.SubElement(quiz, "question", type="cloze")
    name = etree.SubElement(question, "name")
    text = etree.SubElement(name, "text")
    text.text = f"{task}_{user}"
    questiontext = etree.SubElement(question, "questiontext", format="html")
    qtext = etree.SubElement(questiontext, "text")
    # Add subtask prompt if exists
    if subtask_prompt:
        qtext.text = gen_rubric_YKI(txt, user, task, read_txt(task_prompt)+'<br><br>'+read_txt(subtask_prompt), wav_path)
    else:
        qtext.text = gen_rubric_YKI(txt, user, task, read_txt(task_prompt), wav_path)
    generalfeedback = etree.SubElement(question, "generalfeedback", format="html")
    gb_text = etree.SubElement(generalfeedback, "text")
    penalty = etree.SubElement(question, "penalty")
    penalty.text = "0.333"
    hidden = etree.SubElement(question, "hidden")
    hidden.text = "0"
    idnumber = etree.SubElement(question, "idnumber")

    # Create list of samples to mark with the control_set tag
    control_set_sample_list = []
    with open(path_to_control_set_txt, 'r', encoding='utf-8') as f:
        text = f.read().split('\n')
        for line in text:
            line = line.split('/')
            # 1. Subtask in path
            if len(line) == 12:
                control_set_sample_list += [line[-2]+'_'+''.join(line[-4:-2])]
            # 2. No subtask in path
            elif len(line) == 11:
                control_set_sample_list += [line[-2]+'_'+''.join(line[-3])]

    # Add tags
    tags = etree.SubElement(question, "tags")
    tag_list = ["LUKIO_FI", user, task] # list of tags to be added
    #print(user+'_'+task)
    #print(control_set_sample_list)
    if user+'_'+task in control_set_sample_list:
        tag_list += ['control_set']
    if rater_to_sample_dict:
        for rater in rater_to_sample_dict.keys():
            if user+'_'+task in rater_to_sample_dict[rater]:
                tag_list += [rater]
    for tag in tag_list:
        new_tag = etree.SubElement(tags, "tag")
        tag_text = etree.SubElement(new_tag, "text")
        tag_text.text = tag
    return quiz

def getdict_recording_url(recordings_links_file, dict_userid_username, dict_q):
    """
    Make a dictionary to map from Moodle username and question number to the link to the corresponding audio recording
    """
    dict_recording_url = {}
    with open(recordings_links_file, 'r') as f:
        for line in f:
            if line.startswith('save-file'):
                _, url, _, userpath = line.strip().split(' ')
                userid, qnum = int(userpath.split('/')[0].split('-')[2]), int(userpath.split('/')[1].split('-')[0][1:])
                username = dict_userid_username[userid]
                question_num = dict_q[qnum]
                dict_recording_url[(username, question_num)] = url
    return dict_recording_url

def getdict_old_to_new_task_num(moodle_course_id):
    """
    Make a dictionary to map from Moodle question number
    to new task number
    """ 
    if moodle_course_id == '6':
        """
        Suullisen kielitaidon koe (suomi, 9.2.2021)
        B1.1 (9.2.2021)
        """
        dict_old_to_new_task_num={
            "1": "1_a",
            "2": "1_b",
            "3": "1_c",
            "4": "1_d",
            "5": "1_e",
            "6": "1_f",
            "7": "2",
            "8": "3_a",
            "9": "3_b",
            "10": "3_c",
            "11": "3_d",
            "12": "4_a",
            "13": "4_b",
            "14": "4_c",
            "15": "4_d",
            "16": "5",
            "17": "6_a"
        }
    elif moodle_course_id == '13':
        """
        Puhumisen koe (suomi, 03/2021)
        B1.2 (03/2021)
        """
        dict_old_to_new_task_num={
            "1":"0",
            "2": "1_a",
            "3": "1_b",
            "4": "1_c",
            "5": "1_d",
            "6": "1_e",
            "7": "1_f",
            "8": "2",
            "9": "3_a",
            "10": "3_b",
            "11": "3_c",
            "12": "3_d",
            "13": "4_a",
            "14": "4_b",
            "15": "4_c",
            "16": "4_d",
            "17": "5"
        }
    elif moodle_course_id == '15' or \
        moodle_course_id == '16':
        """
        Puhumisen koe B1 (suomi, 04/2021) & Puhumisen koe B1 (suomi, 17.05.2021)
        B1.3 (04/2021) & B1.4 (17.05.2021)
        """
        dict_old_to_new_task_num={
            "1":"0",
            "2": "1_a",
            "3": "1_b",
            "4": "1_c",
            "5": "1_d",
            "6": "1_e",
            "7": "1_f",
            "8": "2",
            "9": "3_a",
            "10": "3_b",
            "11": "3_e",
            "12": "3_f",
            "13": "4_e",
            "14": "4_b",
            "15": "4_c",
            "16": "4_d",
            "17": "5"
        }
    elif moodle_course_id == '14' or \
        moodle_course_id == '17' or \
            moodle_course_id == '19' or \
                moodle_course_id == '20':
        """
        Puhumisen koe (suomi, 04/2021) & Puhumisen koe B2 (suomi, 17.05.2021) &
        Puhumisen koe B2 (suomi, 21.05.2021) & Puhumisen koe B2 (suomi, 26.05.2021)
        B2.1 (04/2021) & B2.2 (17.05.2021) & B2.3 (21.05.2021) & B2.4 (26.05.2021)
        """
        dict_old_to_new_task_num={
            "1":"0",
            "2": "1_a",
            "3": "1_b",
            "4": "1_c",
            "5": "1_d",
            "6": "1_e",
            "7": "1_f",
            "8": "2",
            "9": "7",
            "10": "8_a",
            "11": "8_b",
            "12": "8_c",
            "13": "8_d",
            "14": "6_b"
        }
    return dict_old_to_new_task_num

def rename_old_to_new_task_nums(digitala_student_accounts):
    """
    Rename moodle question numbers to new task numbers
    digitala_student_accounts: Digitala_moodle_accounts.xlsx
    """
    df=pd.read_excel(digitala_student_accounts)
    for f in glob.glob('*.wav'):
        moodle_course_id = df[df.username == f.split('_')[0]].kurssi.item().split('=')[-1]
        moodle_question_num = f.split('.')[0].split('_')[-1]
        dict_old_to_new_task_num = getdict_old_to_new_task_num(moodle_course_id)
        new_task_num = dict_old_to_new_task_num[moodle_question_num]
        os.rename(f, f.split('_')[0]+'_teht_'+new_task_num+'.wav')