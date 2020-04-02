import json
import requests
from urllib.parse import urlencode
import hashlib
import os.path

headers = {
    "Content-Type": "application/json"
}

def get_file(md5):
    filename='./cache/' + md5 + '.json'
    if os.path.isfile(filename):
        with open(filename, 'r') as f:
            fp = f.read()
            return json.loads(str(fp))
    else:
        return None

def write_file(md5, raw):
    filename='./cache/' + md5 + '.json'
    if not os.path.exists(os.path.dirname(filename)):
        try:
            os.makedirs(os.path.dirname(filename))
        except OSError as exc: # Guard against race condition
            if exc.errno != errno.EEXIST:
                raise
    with open(filename, 'w') as f:
        f.write(raw.decode('utf-8'))
        f.close()

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
    res = requests.get(url, params=query, headers=headers)
    if res.status_code == 200:
        return res.content
    else:
        return None

def get_json(url, query=None):
    """ Perform a GET request and return the resulting JSON payload as an object. """
    md5 = hashlib.md5(url.encode('utf-8')).hexdigest()
    file = get_file(md5)
    if (file is None):
        print("Downloading...")
        raw = fetch_data(url, query)
        print("Finished!")
        write_file(md5, raw)
        return json.loads(raw.decode("utf-8"))
    else:
        return file