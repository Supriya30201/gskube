#!/bin/bash
sed -i "s/'HOST': 'localhost',/'HOST': '$DB_HOST',/g" /var/www/html/ServiceOnline/service_online/settings.py
sed -i "s/'USER': 'root',/'USER': '$DB_PORT',/g" /var/www/html/ServiceOnline/service_online/settings.py
sed -i "s/'PASSWORD': 'root',/'PASSWORD': '$DB_PASSWORD',/g" /var/www/html/ServiceOnline/service_online/settings.py
apachectl stop
apachectl start