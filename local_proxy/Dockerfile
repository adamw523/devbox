FROM ubuntu:14.04

RUN apt-get update -q

RUN apt-get install -qy squid vim
ADD squid.conf /etc/squid3/squid.conf

# Make cache dirs
RUN chmod a+w /var/cache
RUN /usr/sbin/squid3 -z -F -N

EXPOSE 3128

# -X verbose debug logging
# -N Don't run in daemon mode
CMD ["/usr/sbin/squid3",  "-N", "-X"]
