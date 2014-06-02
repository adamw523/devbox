#!/bin/bash
STOP=0

cd /seafile/seafile-server-*

start() {
  trap cue_stop SIGINT SIGTERM
  ./seafile.sh start
  ./seahub.sh start-fastcgi
}

cue_stop() {
  STOP=1
}

stop() {
  ./seafile.sh stop
  ./seahub.sh stop
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
