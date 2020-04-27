import json
import requests
from urllib.parse import urlencode
import hashlib
import os.path
import pickle
import codecs

headers = {
    "Content-Type": "application/json"
}

# def download_nhts():
#     chunk_size = 512
#     url = "https://nhts.ornl.gov/assets/2016/download/Csv.zip"
#     save_path = './data/nhts.zip'
#     r = requests.get(url, stream=True)
#     if not os.path.exists(os.path.dirname(save_path)):
#         try:
#             os.makedirs(os.path.dirname(save_path))
#         except OSError as exc: # Guard against race condition
#             if exc.errno != errno.EEXIST:
#                 raise
#     with open(save_path, 'wb') as fd:
#         for chunk in r.iter_content(chunk_size=chunk_size):
#             fd.write(chunk)

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
        print("Running one-time " + f_id + " and writing to cache")
        raw = funct()
        write_file(f_id, raw, folder=folder)
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