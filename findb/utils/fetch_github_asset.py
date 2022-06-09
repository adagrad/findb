import subprocess
import sys
import shutil
import requests


def list_release_files(repo, tag, token):
    resp = requests.get(
        f"https://api.github.com/repos/{repo}/releases/tags/{tag}",
        headers = {
            "authorization": f"Bearer {token}",
            'content-type': 'application/json'
        }
    ).json()
    print(resp)
    print("asstes", [a['name'] for a in resp["assets"]])

    return resp


if __name__ == '__main__':
    token = sys.argv[1]
    repo = sys.argv[2]
    tag = sys.argv[3]
    files = sys.argv[4:]

    resp = list_release_files(repo, tag, token)
    ids = {}
    for file in files:
        match = [a['id'] for a in resp["assets"] if a["name"] == file]
        if len(match) > 0:
            ids[file] = match[0]

    print("found assets", ids)

    for file, id in ids.items():
        try:
            url = f"https://api.github.com/repos/{repo}/releases/assets/{id}"
            print("asset url", url)
            with requests.get(url, stream=True, headers={"authorization": f"Bearer {token}", 'Accept': 'application/octet-stream'}) as r:
                r.raise_for_status()
                r.raw.decode_content = True
                with open(file, 'wb') as f:
                    shutil.copyfileobj(r.raw, f)
        except Exception as e:
            print(e)


def test_list_files():
    list_release_files('adagrad/findb', '2021', open("../../.token").read())