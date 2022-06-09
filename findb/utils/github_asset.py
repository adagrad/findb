import os.path
import subprocess
import sys
import shutil
import requests


def list_releases(repo, token, tag=None):
    resp = requests.get(
        f"https://api.github.com/repos/{repo}/releases",
        headers = {
            "authorization": f"Bearer {token}",
            'content-type': 'application/json'
        }
    )

    assert resp.status_code // 100 == 2, resp.text
    releases = resp.json()

    if tag is not None:
        return [r for r in releases if r['tag_name'] == tag][0]

    return releases


def list_release_files(repo, tag, token):
    release = list_releases(repo, token, tag=tag)
    resp = requests.get(
        release['assets_url'],
        headers = {
            "authorization": f"Bearer {token}",
            'content-type': 'application/json'
        }
    )

    assert resp.status_code // 100 == 2, resp.text
    assets = resp.json()
    print("asstes", [a['name'] for a in assets])
    return release, assets


def download_file(repo, tag, token, asset_name, path='.'):
    release, assets = list_release_files(repo, tag, token)
    path = os.path.join(path, asset_name)
    downloaded = False

    for asset in assets:
        if asset['name'] == asset_name:
            try:
                url = asset['url']
                print("asset url", url)
                with requests.get(url, stream=True, headers={"authorization": f"Bearer {token}", 'Accept': 'application/octet-stream'}) as r:
                    r.raise_for_status()
                    r.raw.decode_content = True
                    with open(path, 'wb') as f:
                        shutil.copyfileobj(r.raw, f)

                downloaded = True
            except Exception as e:
                print(e)

    if not downloaded:
        print(f"File not found {assets}")

    return path

def upload_file(repo, tag, token, asset_file):
    asset_name = os.path.basename(asset_file)
    release, assets = list_release_files(repo, tag, token)
    assets = [a for a in assets if a['name'] == asset_name]
    if len(assets) > 0:
        requests.delete(
            assets[0]['url'],
            headers={
                "authorization": f"Bearer {token}",
                'content-type': 'application/octet-stream'
            },
        )

    url = release['upload_url'].replace("{?name,label}", f"?name={asset_name}")
    resp = requests.patch(
        url,
        headers={
            "authorization": f"Bearer {token}",
            'content-type': 'application/octet-stream'
        },
        data=open(asset_file, 'rb').read()
    )

    print(url, resp.text)
    assert resp.status_code // 100 == 2, f"post failed {resp}, release needs to be a draft release!"
    assert asset_name in [a['name'] for a in list_release_files(repo, tag, token)[1]], "upload failed, file not visible!"
    return resp.json()


if __name__ == '__main__':
    action = sys.argv[1]
    token = sys.argv[2]
    repo = sys.argv[3]
    tag = sys.argv[4]
    assets = sys.argv[5:]

    for asset in assets:
        if action == 'GET':
            download_file(repo, tag, token, asset)
        elif action == 'PUT':
            upload_file(repo, tag, token, asset)


def test_list_files():
    assert isinstance(list_release_files('adagrad/findb', '2021', open("../../.token").read()), tuple)


def test_upload():
    assert isinstance(upload_file('adagrad/findb', '2021', open("../../.token").read(), "../data/test.csv"), dict)


def test_download():
    if os.path.exists('/tmp/test.csv'):
        os.remove('/tmp/test.csv')

    download_file('adagrad/findb', '2021', open("../../.token").read(), "test.csv", "/tmp/")
    assert os.path.exists('/tmp/test.csv')