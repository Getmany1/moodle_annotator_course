#import requests
from datetime import datetime
import os
import glob
#import urllib3
from utils import *
#from my_cookies import cookies, headers # personal cookies from moodle (convert curl to python with https://curl.trillworks.com/)
#urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

## Parameters
audio_format = 'wav' # audio format of audio recordings, default: 'ogg'
parent_dir = os.path.join('y:',os.sep,'DigiTala_2019-2023',
                                  'yki_fin_mono_16k_sorted') # name of folder which will contain the collected data
output_dir = 'outputs' # name of folder where to put the generated xml quizes
html_temp_fname = 'template_YKI.html' # html template file for rater quiz
server_path = "http://digitalamoodle.aalto.fi/digi_rsrc/moodle_annotator_course/" # path to server
                # where the uploaded audio responses are located
path_to_control_set_txt = "YKI-S2-control-set.txt" # path to a txt file with th control set

## Create quiz

# Read HTML template
with open(html_temp_fname, 'r', encoding='utf8') as temp:
    txt = temp.read()

# Create element
quiz = etree.Element("quiz")

# Generate quiz
for f in glob.glob(parent_dir+'/*/*/*/*.'+audio_format, recursive=True):
    dirpath, wavfile = os.path.split(f)
    level, task, user = dirpath.split(os.sep)[-3:]
    # Exclude tasks 2 and 3 (keskitaso)
    if level=='yt' or (level=='kt' and task not in ['2','3']):
        # Separate task 1 ylin taso and task 1 keskitaso from each other
        # 1 keskitaso = 1.1; 1 ylin taso = 1.2
        if task == '1':
            if 'kt' in dirpath:
                task = '1.1'
            elif 'yt' in dirpath:
                task = '1.2'
        wav_path = server_path + os.path.join('/'.join(dirpath.split(os.sep)[-4:]), wavfile).replace("\\","/")
        task_prompt = os.path.abspath(os.sep.join(dirpath.split(os.sep)[:-1])+os.sep+'task_prompt.txt')

        # Add transcript if such exists. Note: several transcripts (transcript.txt / transcript(1).txt)
        if os.path.isfile(os.path.abspath(dirpath+os.sep+'transcript.txt')):
            transcript = os.path.abspath(dirpath+os.sep+'transcript.txt')
        else:
            transcript = None

        generate_quiz_xml_YKI(txt, task, user, wav_path, task_prompt, quiz, path_to_control_set_txt)

# Save the quiz in a moodle xml file
rater_quiz_xml_fname = 'raterquiz_YKI_' + datetime.now().strftime("%d.%m.%Y_%H-%M-%S") + '.xml'
quiz.getroottree().write(os.path.join(output_dir, rater_quiz_xml_fname), encoding='utf8',  xml_declaration=True)