import requests
import urllib3
from my_cookies import cookies, headers # personal cookies from moodle (convert curl to python with https://curl.trillworks.com/)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def write2disk(file, name):
    with open(f'{name}.ogg', 'wb') as f:
        f.write(file)


with open('Suullisenkielitaidonkoe,suomi-steps.txt', 'r') as file:
    for line in file:
        if line.startswith('save-file'):
            _, url, _, userpath = line.strip().split(' ')
            usr, qnum = userpath.split('/')[0], userpath.split('/')[1]
            fname  = f"{usr}_{qnum}"
            r = requests.get(url, allow_redirects=True, headers=headers, cookies=cookies, verify=False)
            write2disk(r.content, fname)
            print(url, userpath)

            # break