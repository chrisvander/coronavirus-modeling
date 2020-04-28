import json
import requests
from urllib.parse import urlencode
import hashlib
import os.path
import pickle
import codecs
from tqdm import tqdm
import zipfile
import shutil

headers = {
    "Content-Type": "application/json"
}

def init_nhts():
    if os.path.exists('./data/nhts/trippub.csv'):
        return
    dirpath = './data/nhts/'
    if os.path.exists(dirpath) and os.path.isdir(dirpath):
        shutil.rmtree(dirpath)
    download_nhts()


def download_nhts():
    print("Downloading CSV files from NHTS...")
    chunk_size = 512
    url = "https://nhts.ornl.gov/assets/2016/download/Csv.zip"
    save_path = './data/nhts.zip'
    r = requests.get(url, stream=True)
    if not os.path.exists(os.path.dirname(save_path)):
        try:
            os.makedirs(os.path.dirname(save_path))
        except OSError as exc: # Guard against race condition
            if exc.errno != errno.EEXIST:
                raise
    file_size = int(requests.head(url).headers["Content-Length"])
    with open(save_path, 'wb') as fd:
        for chunk in tqdm(r.iter_content(chunk_size=chunk_size), total=int(file_size/chunk_size)):
            fd.write(chunk)
    print('Unzipping...')
    with zipfile.ZipFile('./data/nhts.zip', 'r') as zip_ref:
        zip_ref.extractall('./data/nhts')

def get_file(f_id, folder=None):
    md5 = hashlib.md5(f_id.encode('utf-8')).hexdigest()
    filename='./cache/' + md5
    if folder:
        filename='./cache/' + folder + '/' + md5
    if os.path.isfile(filename):
        with open(filename, 'rb') as f:
            return pickle.load(f)
    else:
        return None

def write_file(f_id, raw, folder=None):
    md5 = hashlib.md5(f_id.encode('utf-8')).hexdigest()
    filename='./cache/' + md5
    if folder:
        filename='./cache/' + folder + '/' + md5
    if not os.path.exists(os.path.dirname(filename)):
        try:
            os.makedirs(os.path.dirname(filename))
        except OSError as exc: # Guard against race condition
            if exc.errno != errno.EEXIST:
                raise
    with open(filename, 'wb') as f:
        pickle.dump(raw, f, protocol=pickle.HIGHEST_PROTOCOL)

def cache(f_id, funct, folder=None):
    res = get_file(f_id, folder=folder)
    if res is None:
        print("> Caching: " + f_id)
        raw = funct()
        write_file(f_id, raw, folder=folder)
        print("\t> Done")
        return raw
    return res

def parse_query(query):
    """ Convert all lists to strings within a given query dict. """
    ret = {}
    for k, v in query.items():
        if isinstance(v, list):
            ret[k] = ",".join(v)
        else:
            ret[k] = v
    return ret

def fetch_data(url, query=None):
    print("Fetching " + url)
    res = requests.get(url, params=query, headers=headers)
    if res.status_code == 200:
        return res.content.decode("utf-8")
    else:
        return None

def get_json(url, query=None):
    """ Perform a GET request and return the resulting JSON payload as an object. """
    return json.loads(cache(url, lambda: fetch_data(url, query), folder='web_requests'))