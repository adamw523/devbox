FROM ubuntu:14.04

RUN apt-get update -q --fix-missing && echo "hi"

# requirements
RUN apt-get -qy install apache2 php5 libapache2-mod-php5 unzip
RUN apt-get -qy install curl

# add user
RUN useradd -m %(user)s

ENV APACHE_RUN_USER %(user)s
ENV APACHE_RUN_GROUP %(user)s
ENV APACHE_LOG_DIR /var/log/apache2
ENV APACHE_LOCK_DIR /var/run/apache2
ENV APACHE_PID_FILE /var/run/apache2.pid

RUN curl http://icecoder.net/download-zip -o /tmp/icecoder.zip

RUN cd /var/www/html && unzip -o /tmp/icecoder.zip
RUN cd /var/www/html && mv ICEco* icecoder
RUN chown %(user)s:%(user)s -R /var/www
RUN mkdir /var/www/html/icecoder/projects && chown %(user)s:%(user)s -R \
  /var/www/html/icecoder/projects \
  && chmod g+s /var/www/html/icecoder/projects

# Configuration
RUN sed -i 's/\(docRoot[^>\ ]*>\ \)[^,]*/\1"%(directory_esc)s"/' /var/www/html/icecoder/lib/config___settings.php
RUN sed -i 's/\(loginRequired[^>\ ]*>\ \)[^,]*/\1false/' /var/www/html/icecoder/lib/config___settings.php

CMD ["/usr/sbin/apache2", "-D", "FOREGROUND"]
