import hashlib
from urllib import request


def sha256sum(filename):
    h = hashlib.sha256()
    b = bytearray(128*1024)
    mv = memoryview(b)
    with open(filename, 'rb', buffering=0) as f:
        for n in iter(lambda : f.readinto(mv), 0):
            h.update(mv[:n])
    return h.hexdigest()


def get_remote_hash(url):
    r = request.urlopen(url)
    return r.read().decode().split()[0]


def download_file(url, dest):
    r = request.urlopen(url)
    with open(dest, "wb") as fh:
        fh.write(r.read())
