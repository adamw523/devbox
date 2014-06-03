#!/bin/bash
STOP=0

cd /seafile/seafile-cli-*

start() {
  trap cue_stop SIGINT SIGTERM

  if [ ! -d "%(sync_path)s" ]; then
    # initialize if not initialized
    mkdir "%(sync_path)s"
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
