#!/bin/bash
sed -i "s/'HOST': 'localhost',/'HOST': '$DB_HOST',/g" /var/www/html/ServiceOnline/service_online/settings.py
sed -i "s/'USER': 'root',/'USER': '$DB_PORT',/g" /var/www/html/ServiceOnline/service_online/settings.py
sed -i "s/'PASSWORD': 'root',/'PASSWORD': '$DB_PASSWORD',/g" /var/www/html/ServiceOnline/service_online/settings.py
git clone http://$GIT_USERNAME:$GIT_PASSWORD@gitlab.gslab.com/sanket.modi/ServiceOnline.git
cp -r ServiceOnline /var/www/html/
apachectl stop
apachectl start
if [ $# -gt 0 ]; then
  exec "$@"
fi