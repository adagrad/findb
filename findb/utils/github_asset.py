import os.path
import re
import subprocess
import sys
import shutil
from datetime import datetime
from time import sleep

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
    for i in range(5):
        resp = requests.patch(
            url,
            headers={
                "authorization": f"Bearer {token}",
                'content-type': 'application/octet-stream'
            },
            data=open(asset_file, 'rb').read()
        )

        if resp.status_code // 100 == 2:
            break

        print("retry upload after exception", resp.text)
        sleep(i * 10)

    print(url, resp.text)
    assert resp.status_code // 100 == 2, f"post failed {resp}, release needs to be a draft release!"
    assert asset_name in [a['name'] for a in list_release_files(repo, tag, token)[1]], "upload failed, file not visible!"
    return resp.json()


def copy_release_files(repo, tag_src, tag_dest, token, replace_existing=False):
    src_release, src_assets = list_release_files(repo, tag_src, token)
    tgt_release, tgt_assets = list_release_files(repo, tag_dest, token)

    if not replace_existing:
        existing_files = [a['name'] for a in tgt_assets]
        src_assets = [a for a in src_assets if a['name'] not in existing_files]

    for src in src_assets:
        file = download_file(repo, tag_src, token, src['name'])
        if os.path.exists(file):
            upload_file(repo, tag_dest, token, src['name'])
            os.remove(file)
        else:
            print("error file not found", file)


def bump_year(repo, tag, token, file):
    year_ex = re.compile("\d{4}")
    release, assets = list_release_files(repo, tag, token)
    file_extensions = [".db", ".tgz", ".csv"]
    for asset in assets:
        for ext in file_extensions:
            file_no_ext = file.replace(ext, '')

        if asset['name'].startswith(file_no_ext):
            download_file(repo, tag, token, asset['name'])
            # separate asset name and year.
            years = [int(y) for y in year_ex.findall(asset['name'])]
            # find max year or empty
            year = max(years) if len(years) > 0 else None
            # rename file and upload with new year
            new_name = asset['name'].replace(str(year), str(year + 1)) if year is not None else asset['name'].replace(file_no_ext, f"{file_no_ext}{datetime.now().year}")

            print("rename", asset['name'], new_name)
            os.rename(asset['name'], new_name)
            upload_file(repo, tag, token, new_name)


if __name__ == '__main__':
    action = sys.argv[1]
    token = sys.argv[2]
    repo = sys.argv[3]
    tag = sys.argv[4]
    files = sys.argv[5:]

    for file in files:
        if action == 'GET':
            download_file(repo, tag, token, file)
        elif action == 'PUT':
            upload_file(repo, tag, token, file)
        elif action == 'BUMP_YEAR':
            bump_year(repo, tag, token, file)
        elif action == 'COPY':
            stag, ttag = tag.split("|")
            copy_release_files(repo, stag, ttag, False)
        else:
            print("unknown action", action, file)


def test_list_files():
    assert isinstance(list_release_files('adagrad/findb', '2021', open("../../.token").read()), tuple)


def test_upload():
    assert isinstance(upload_file('adagrad/findb', '2021', open("../../.token").read(), "../data/test.csv"), dict)


def test_download():
    if os.path.exists('/tmp/test.csv'):
        os.remove('/tmp/test.csv')

    download_file('adagrad/findb', '2021', open("../../.token").read(), "test.csv", "/tmp/")
    assert os.path.exists('/tmp/test.csv')


def test_bump_year():
    bump_year('adagrad/findb', '2021', open("../../.token").read(), "test.csv")


def test_copy():
    copy_release_files('adagrad/findb', 'db', '2021', open("../../.token").read())