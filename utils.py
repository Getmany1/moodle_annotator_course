from xml.dom.minidom import parse
import os
import re

def natural_sort_key(s):
    return [int(text) if text.isdigit() else text.lower()
            for text in re.split(re.compile('([0-9]+)'), s)]

def getdict_userid_username():
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
    Returns:
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
                # search for @@PLUGINFILE@@, which contains the name of prompt audio or image
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
    parent_dir = os.path.join('moodle_quiz')
    os.mkdir(parent_dir)
    for tasknum in dict_task_prompt.keys():
        os.mkdir(os.path.join(parent_dir,str(tasknum)))
        with open(os.path.join(parent_dir,str(tasknum),'task_prompt.txt'), 'w', encoding='utf-8') as f:
            f.write(dict_task_prompt[tasknum])
        for qnum in dict_question_prompt.keys():
            if tasknum == int(qnum[:-1]):
                os.mkdir(os.path.join(parent_dir,str(tasknum),qnum))
                with open(os.path.join(parent_dir,str(tasknum),qnum,'prompt.txt'), 'w', encoding='utf-8') as f:
                    f.write(dict_question_prompt[qnum])