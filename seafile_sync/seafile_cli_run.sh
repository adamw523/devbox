#!/bin/bash
STOP=0
HOME=/home/%(user)s

cd /seafile/seafile-cli-*

start() {
  trap cue_stop SIGINT SIGTERM

  if [ ! -d "/home/%(user)s/.ccnet" ]; then
    # initialize if not initialized
    ./seaf-cli init -d ~/.seafile-client
    ./seaf-cli start
    ./seaf-cli sync -l "%(sync_library_id)s" -s  "%(protocol)s://%(server)s:%(port)s" -d "%(sync_path)s" -u "%(username)s" -p "%(password)s"
  else
    # just start
    ./seaf-cli start
  fi
}

cue_stop() {
  STOP=1
}

stop() {
  ./seaf-cli stop
  exit 0
}

start

if [ "$STOP" -eq 1 ]; then
  stop
fi

trap stop SIGINT SIGTERM

while [ 1 ]; do
  sleep 10
done
