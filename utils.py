from xml.dom.minidom import parse
import os
import re
import shutil
from string import Template
from lxml import etree

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
    
def getdicts_question_task():
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
                prompt = q.getElementsByTagName("questiontext")[0].firstChild.nodeValue # task_prompt.txt / prompt.txt
                q_name = q.getElementsByTagName("name")[0].firstChild.nodeValue
                if q_name.split(' ')[1].isdigit(): # Tehtävä X (1,2...)
                    dict_task_prompt[tasknum] = prompt

                    # In pilot test, tasks 3 and 8 do not have sub-tasks!!
                    if tasknum == 3:
                        dict_question_prompt[str(tasknum)+'a'] = prompt
                        question_list.append(str(tasknum)+'a')
                    if tasknum == 8 and q.getAttribute("id") == "3014":
                        dict_question_prompt[str(tasknum)+'a'] = prompt
                        question_list.append(str(tasknum)+'a')

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

def gen_rubric(student, question, t_prompt, q_prompt, wavpath):
    s = Template(txt)
    tt = s.substitute(StudentID=student, QuestionID=question, TaskPrompt=t_prompt, QuestionPrompt=q_prompt, Wav_path=wavpath)
    return tt
    

def generate_quiz_xml(task, ques_var, user, wav_path, task_prompt, question_prompt, quiz):
    """Generate a Cloze-type Moodle question quiz"""
    
    question = etree.SubElement(quiz, "question", type="cloze")
    name = etree.SubElement(question, "name")
    text = etree.SubElement(name, "text")
    text.text = f"{task}_{ques_var}_{user}"
    questiontext = etree.SubElement(question, "questiontext", format="html")
    qtext = etree.SubElement(questiontext, "text")
    qtext.text = gen_rubric(user, ques_var, read_txt(task_prompt), read_txt(question_prompt), wav_path)
    generalfeedback = etree.SubElement(question, "generalfeedback", format="html")
    gb_text = etree.SubElement(generalfeedback, "text")
    penalty = etree.SubElement(question, "penalty")
    penalty.text = "0.333"
    hidden = etree.SubElement(question, "hidden")
    hidden.text = "0"
    idnumber = etree.SubElement(question, "idnumber")
    return quiz