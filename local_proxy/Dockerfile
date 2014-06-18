FROM centos:latest

RUN yum install -y squid vim
ADD squid.conf /etc/squid/squid.conf

# Make cache dirs
RUN chmod a+w /var/cache
RUN squid -z -F

EXPOSE 3128

# -X verbose debug logging
# -N Don't run in daemon mode - important for docker
CMD squid -N -X
