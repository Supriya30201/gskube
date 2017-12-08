FROM service_online_base:latest
RUN git clone http://@GIT_USERNAME@:@GIT_PASSWORD@@gitlab.gslab.com/sanket.modi/ServiceOnline.git
RUN cp -r ServiceOnline /var/www/html/
COPY apache2.conf /tmp/
RUN cat /tmp/apache2.conf >> /etc/apache2/apache2.conf
RUN chmod 777 /ServiceOnline/launch.sh
ENTRYPOINT ["/ServiceOnline/launch.sh"]