#!/bin/bash
dnf update -y --security
dnf install -y nginx
cat <<EOF > /etc/nginx/conf.d/catch-all.conf
log_format detailed_log '$remote_addr - $remote_user [$time_local] '
                        '"$request" $status $body_bytes_sent '
                        '"$http_referer" "$http_user_agent" '
                        'Request: "$request_body" '
                        'Request Headers: "$http_host $http_x_forwarded_for" '
                        'Response Headers: "$sent_http_content_type"';
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    server_name _;
    access_log /var/log/nginx/access.log detailed_log;
    error_log /var/log/nginx/error.log debug;
    location / {
        default_type text/html;
        return 200 '<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Static Response</title>
</head>
<body>
    <p>This is a dynamic response for all paths and all server names.</p>
    <p>Server: \$hostname</p>
    <p>Requested Host: \$host</p>
    <h2>Cookies:</h2>
    <pre>\$http_cookie</pre>
    <h2>Headers:</h2>
    <pre>\$http_user_agent</pre>
    <pre>\$http_referer</pre>
</body>
</html>';
    }
}
EOF

systemctl start nginx
systemctl enable nginx