FROM nginx:latest

COPY default.conf /etc/nginx/conf.d/default.conf
COPY static/ /usr/share/nginx/html/