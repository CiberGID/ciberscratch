FROM alpine

# add bash
RUN apk add --no-cache bash

# add openssh and clean
RUN apk add --update openssh && rm -rf /tmp/* /var/cache/apk/*

# add entrypoint script
ADD docker-entrypoint.sh /usr/local/bin

#make sure we get fresh keys
RUN rm -rf /etc/ssh/ssh_host_rsa_key /etc/ssh/ssh_host_dsa_key

#change root passwd
RUN echo "root:EFhObKJrE4pwQkiTUsij8w=" | chpasswd

EXPOSE 22
ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["/usr/sbin/sshd","-D"]

