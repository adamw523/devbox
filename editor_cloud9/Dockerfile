FROM ubuntu:14.04
RUN export http_proxy=%(proxy_url)s; \
    apt-get update -q --fix-missing

## Cloud9
RUN export http_proxy=%(proxy_url)s; \
    apt-get install -qy git nodejs npm

CMD ["/usr/bin/supervisord"]
