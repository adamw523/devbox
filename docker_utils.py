import hashlib
import posixpath
import random

from fabric.api import put, run
from fabric.contrib.files import exists

def bridge_ip():
    ip = run("ifconfig docker0 |grep 'inet addr' |awk -F: '{print $2}' |awk '{print $1}'")
    return ip

def put_if_changed(local_path, remote_path):
    # create random temporary path
    hasher = hashlib.sha1()
    hasher.update(str(random.random()))
    temp_name = hasher.hexdigest()
    temp_path = posixpath.join('/tmp', temp_name)

    exists_ = exists(remote_path)
    if exists_:
        # put to temp location
        put(local_path, temp_path)

        # get hashes
        hash_old = run('sha1sum %s | cut -d \' \' -f 1' % (remote_path))
        hash_new = run('sha1sum %s | cut -d \' \' -f 1' % (temp_path))

        if(hash_old == hash_new):
            run('rm %s' % (temp_path))

        else:
            run('mv %s %s' % (temp_path, remote_path))

    else:
        put(local_path, remote_path)

