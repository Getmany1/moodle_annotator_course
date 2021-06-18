#import requests
from datetime import datetime
import os
import glob
import pickle as pkl
#import urllib3
from utils import *
#from my_cookies import cookies, headers # personal cookies from moodle (convert curl to python with https://curl.trillworks.com/)
#urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

## Parameters
audio_format = 'wav' # audio format of audio recordings, default: 'ogg'
parent_dir = os.path.join('y:',os.sep,'DigiTala_2019-2023',
                                  'digitala_fi_lukio_16k_sorted') # name of folder which will contain the collected data
parent_dir = os.path.join('digitala_fi_lukio_16k_sorted') # name of folder which will contain the collected data
output_dir = 'outputs' # name of folder where to put the generated xml quizes
html_temp_fname = 'template_FI.html' # html template file for rater quiz
server_path = "http://digitalamoodle.aalto.fi/digi_rsrc/moodle_annotator_course/" # path to server
                # where the uploaded audio responses are located
path_to_control_set_txt = "Digitala-fi-lukio-control-set.txt" # path to a txt file with th control set
with open('lukio_raters.pickle','rb') as f:
    rater_to_sample_dict = pkl.load(f)  # dictionary to map each rater to their samples to be rated

## Create quiz

# Read HTML template
with open(html_temp_fname, 'r', encoding='utf8') as temp:
    txt = temp.read()

# Create element
quiz = etree.Element("quiz")

# Generate quiz
for f in glob.glob(parent_dir+'/**/*.'+audio_format, recursive=True):
    dirpath, wavfile = os.path.split(f)
    # 1. Subtask exists
    if len(dirpath.split(os.sep))==4:
        task, subtask, user = dirpath.split(os.sep)[-3:]

    # 2. There is no subtask
    else:
        task, user = dirpath.split(os.sep)[-2:]
        subtask = None

    # Exclude microphone test
    if task!='0':
        wav_path = server_path + f.replace("\\","/")
        task_prompt = os.path.abspath(os.sep.join(dirpath.split(os.sep)[:2])+os.sep+'task_prompt.txt')
        subtask_prompt = None
        if len(dirpath.split(os.sep))==4:
            subtask_prompt = os.path.abspath(os.sep.join(dirpath.split(os.sep)[:3])+os.sep+'prompt.txt')

        # Add transcript if such exists. Note: several transcripts (transcript.txt / transcript(1).txt)
        if os.path.isfile(os.path.abspath(dirpath+os.sep+'transcript.txt')):
            transcript = os.path.abspath(dirpath+os.sep+'transcript.txt')
        else:
            transcript = None

        generate_quiz_xml_LUKIO(txt, task, subtask, user, wav_path, task_prompt, subtask_prompt, quiz, path_to_control_set_txt, rater_to_sample_dict)

# Save the quiz in a moodle xml file
rater_quiz_xml_fname = 'raterquiz_LUKIO_' + datetime.now().strftime("%d.%m.%Y_%H-%M-%S") + '.xml'
quiz.getroottree().write(os.path.join(output_dir, rater_quiz_xml_fname), encoding='utf8',  xml_declaration=True)