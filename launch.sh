#!/bin/bash
sed -i "s/'HOST': 'localhost',/'HOST': '$DB_HOST',/g" /var/www/html/ServiceOnline/service_online/settings.py
sed -i "s/'USER': 'root',/'USER': '$DB_USER',/g" /var/www/html/ServiceOnline/service_online/settings.py
sed -i "s/'PASSWORD': 'root',/'PASSWORD': '$DB_PASSWORD',/g" /var/www/html/ServiceOnline/service_online/settings.py
sed -i 's#LOG_FILE_DIR = "logs/"#LOG_FILE_DIR = "/var/www/html/ServiceOnline/logs/"#g' /var/www/html/ServiceOnline/core/log_configuration.py
sudo chmod u+x /var/www/html/ServiceOnline/service_online/wsgi.py
mkdir /var/www/html/ServiceOnline/logs
chmod 777 -R /var/www/html/ServiceOnline/logs
a2enmod ssl
apachectl stop
apachectl start
tail -f /dev/null