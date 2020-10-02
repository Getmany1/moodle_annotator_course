import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


cookies = {
    
}

headers = {

}



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