import json
import os
import sys
import zipfile

import requests
import argparse
import glob

USERNAME = 'TAI_E_USERNAME'
PASSWORD = 'TAI_E_PASSWORD'
SUBMIT_FILES = 'submit_files.json'
PWD = sys.path[0]

UPLOAD_API = 'https://oj.pascal-lab.net/api/filesys/upload'
CREATE_API = 'https://oj.pascal-lab.net/api/submit/create'
LOGIN_API = 'https://oj.pascal-lab.net/api/user/login'
PROBLEM_API_FMT = 'https://oj.pascal-lab.net/api/problem/query?problemCode=Tai-e-{}'

login_payload = {"username": "", "password": ""}
create_payload = {"problemCode": "Tai-e-x", "judgeTemplateId": "", "zipFileId": ""}

decoder = json.JSONDecoder()
encoder = json.JSONEncoder()


def login(username, password) -> requests.Session:
    session = requests.Session()
    session.headers['user-agent'] = 'Mozilla/5.0'
    login_payload['username'] = username
    login_payload['password'] = password
    r = session.post(LOGIN_API, data=encoder.encode(login_payload), headers={'content-type': 'application/json'})
    login_dict = decoder.decode(r.text)
    if login_dict['code'] != 0:
        sys.exit(f'Login failed! Source response: {login_dict}')
    return session


def submit(session: requests.Session, aid, path):
    problem_api = PROBLEM_API_FMT.format(aid)
    r = session.get(problem_api)
    problem_dict = decoder.decode(r.text)
    pid = problem_dict['data']['judgeTemplates'][0]['id']

    with open(path, 'rb') as fd:
        r = session.post(UPLOAD_API, files={'file': (fd.name, fd, 'application/zip')})
    zip_dict = decoder.decode(r.text)
    zid = zip_dict['data']['id']
    print()
    print(f'ZipFileId: {zid}')

    create_payload['problemCode'] = f"Tai-e-{aid}"
    create_payload['judgeTemplateId'] = str(pid)
    create_payload['zipFileId'] = zid
    r = session.post(CREATE_API, data=encoder.encode(create_payload), headers={'content-type': 'application/json'})
    create_dict = decoder.decode(r.text)
    sid = create_dict['data']

    print()
    print("Submitted!")
    print()
    print(f"Status at: https://oj.pascal-lab.net/submission/{sid}")


def zip_up(path, aid) -> str:
    with open(os.path.join(PWD, SUBMIT_FILES), 'r') as fd:
        files = decoder.decode(fd.read())[aid - 1]
    result = []

    for file in files:
        found = glob.glob(f'**/{file}', root_dir=path, recursive=True)
        if len(found) == 0:
            sys.exit(f'{file} not found!')
        elif len(found) > 1:
            sys.exit(f'Found multiple {file}!\n{found}')
        result.append(os.path.join(path, found[0]))

    print('Found the following files:')
    for file in result:
        print(f'- {file.replace(path, ".../")}')

    zip_path = os.path.join(PWD, f'Submit_A{aid}.zip')
    with zipfile.ZipFile(zip_path, 'w') as zf:
        for file in result:
            zf.write(file, arcname=os.path.split(file)[-1])
    print(f'Zipped at {zip_path}')
    print()

    return zip_path


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('aid', help='Assignment ID (from 1 to 8)', type=int)
    parser.add_argument('--src', '-s', help='src directory of the assignment, for auto zipping', type=str)
    parser.add_argument('--file', '-f', help='Submit file path (end with .zip)', type=str)
    args = parser.parse_args()

    _aid = args.aid
    _file = args.file
    _src = args.src
    if not 1 <= _aid <= 8:
        sys.exit(f'Assignment ID {_aid} out of 1~8')
    if _src != '':
        if not os.path.exists(_src):
            sys.exit(f'src path [{_src}] not exist!')
        _file = zip_up(_src, _aid)

    if not _file.endswith('.zip'):
        sys.exit(f'Upload file not zip file!')

    if USERNAME not in os.environ:
        sys.exit(f'Lack of {USERNAME}')
    if USERNAME not in os.environ:
        sys.exit(f'Lack of {PASSWORD}')

    _username = os.environ[USERNAME]
    _password = os.environ[PASSWORD]
    _session = login(_username, _password)

    print(f'Submitting to Tai-e A{_aid}.')
    print(f'> Upload file: {_file}')
    print(f'> Username: {_username}')

    _ans = input('Ready to submit? (Y/n) ')
    print()
    if _ans.lower().startswith('y'):
        submit(_session, _aid, _file)
