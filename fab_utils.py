import hashlib
import posixpath
import random

from fabric.api import put, run
from fabric.contrib.files import exists
from fabtools.files import is_dir
from os.path import basename

def put_if_changed(local_path, remote_path):
    # create random temporary path
    hasher = hashlib.sha1()
    hasher.update(str(random.random()))
    temp_name = hasher.hexdigest()
    temp_path = posixpath.join('/tmp', temp_name)
    target_path = remote_path
    if is_dir(remote_path):
        target_path = posixpath.join(remote_path, basename(local_path))

    exists_ = exists(remote_path)
    if exists_:
        # put to temp location
        put(local_path, temp_path)

        # get hashes
        hash_old = run('shasum %s | cut -d \' \' -f 1' % (target_path))
        hash_new = run('shasum %s | cut -d \' \' -f 1' % (temp_path))

        if(hash_old == hash_new):
            run('rm %s' % (temp_path))
        else:
            run('mv %s %s' % (temp_path, target_path))

    else:
        put(local_path, target_path)

