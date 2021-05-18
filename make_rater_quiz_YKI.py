import requests
from datetime import datetime
import os
import glob
#import urllib3
from utils import *
#from my_cookies import cookies, headers # personal cookies from moodle (convert curl to python with https://curl.trillworks.com/)
#urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

## Parameters
audio_format = 'wav' # audio format of audio recordings, default: 'ogg'
parent_dir = 'moodle_quiz_yki_test' # name of folder which will contain the collected data
output_dir = 'outputs' # name of folder where to put the generated xml quizes
html_temp_fname = 'template_YKI.html' # html template file for rater quiz
server_path = "http://digitalamoodle.aalto.fi/digi_rsrc/moodle_annotator_course/" # path to server
                # where the uploaded audio responses are located

## Create quiz

# Read HTML template
with open(html_temp_fname, 'r', encoding='utf8') as temp:
    txt = temp.read()

# Create element
quiz = etree.Element("quiz")

# Generate quiz
for f in glob.glob(parent_dir+'/*/*/*/*.'+audio_format, recursive=True):
    dirpath, wavfile = os.path.split(f)
    _, _, task, user = dirpath.split(os.sep)
    wav_path = server_path + os.path.join(dirpath, wavfile)
    task_prompt = os.path.abspath(os.sep.join(dirpath.split(os.sep)[:-1])+os.sep+'task_prompt.txt')

    # Add transcript if such exists. Note: several transcripts (transcript.txt / transcript(1).txt)
    if os.path.isfile(os.path.abspath(dirpath+os.sep+'transcript.txt')):
        transcript = os.path.abspath(dirpath+os.sep+'transcript.txt')
    else:
        transcript = None

    generate_quiz_xml_YKI(txt, task, user, wav_path, task_prompt, quiz)

# Save the quiz in a moodle xml file
rater_quiz_xml_fname = 'raterquiz_YKI_' + datetime.now().strftime("%d.%m.%Y_%H-%M-%S") + '.xml'
quiz.getroottree().write(os.path.join(output_dir, rater_quiz_xml_fname), encoding='utf8',  xml_declaration=True)