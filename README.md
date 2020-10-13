# moodle_annotator_course

TODO:

1) (DONE) User dictionary: maps from user ID to user name. && question id/ question number

2) (DONE) Download audio files into structured folders

    (Category)/Task/Question/Student/
    
    e.g. collected_form/0/0_1/joens_3hv
    
3) Convert ogg -> wav

4) modify the rubric quiz template to include task info + student audio response.

Files needed to download/create manually:
1) Text file with links for students' audio responses
- Go to the quiz page in digitalamoodle.aalto.fi
- press the cogwheel -> "Export attempts" -> "Download review sheets in bulk" (at the end of the page) -> "bulk download steps file"
- Put the downloaded file into the the same folder where "main.py" is located. The default name for the file is "quiz.txt" (if other filename, change the variable "recordings_links_file" in main.py)
2) XML backup files from the student quiz.
- Link for download backup: https://digitalamoodle.aalto.fi/pluginfile.php?forcedownload=1&file=%2F133%2Fbackup%2Factivity%2Fvarmuuskopio-moodle2-activity-42-quiz42-20201002-1311.mbz
- Unzip into "backup" folder
3) Html copy of the quiz.
- Go to "Suullisen kielitaidon koe (suomi)" -> "Kysymyspankki" -> "Vie" -> "Vie kysymykset tiedostoon" -> choose "XHTML-muotoinen" -> press "Vie kysymykset tiedostoon"
- Put the downloaded file into the same folder where "main.py" is located. The default name for the file is "student_quiz.html" (if other filename, change the variable "html_filename" in main.py)
4) Python file with cookies "my_cookies.py". The file should contain variables "cookies" and "headers". To get the cookies, you can:
- log in to the digitalamoodle.aalto.fi (or open any link from quiz.txt)
- go to DevTools in your browser (cntrl+shift+i in Chrome Win10)
- go to the "Network" tab
- ctrl-click a request, "Copy as cURL (bash)".
- paste tp https://curl.trillworks.com/ to convert cURL -> Python cookies.
- Copy the variables "cookies" and "headers" to "my_cookies.py". The file should be located in the the same folder where "main.py" is located.
