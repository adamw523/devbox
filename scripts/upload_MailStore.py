import boto.s3

def upload_cb(complete, total):
    print " %s / %s - %s" % (complete, total, str(float(complete) / float(total)))

filename = '/data/MailStore.zip'

conn = boto.connect_s3()
bucket = conn.get_bucket('adamw523_backups')

k = boto.s3.key.Key(bucket)
k.key = 'MailStore.zip'
k.set_contents_from_filename(filename, cb=upload_cb, num_cb=1000)
