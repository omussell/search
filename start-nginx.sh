#!/bin/sh

# Create directory for certificates if it doesn't exist
mkdir -p /etc/nginx/certs

# Generate a self-signed certificate
openssl req -x509 -newkey rsa:4096 -keyout /etc/nginx/certs/domain.key -out /etc/nginx/certs/domain.crt -days 365 -subj '/CN=localhost' -nodes

# Start nginx
nginx -g 'daemon off;'
