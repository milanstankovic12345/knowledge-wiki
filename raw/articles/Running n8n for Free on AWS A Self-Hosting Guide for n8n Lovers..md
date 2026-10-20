---
title: "Running n8n for Free on AWS: A Self-Hosting Guide for n8n Lovers."
source: "https://medium.com/@mmartinmainan/running-n8n-for-free-on-aws-a-self-hosting-guide-for-n8n-lovers-4e367727f45e"
author:
  - "[[Martin Maina]]"
published: 2025-05-22
created: 2026-10-20
description: "Martin Maina highlighted"
tags:
  - "clippings"
---
# Running n8n for Free on AWS: A Self-Hosting Guide for n8n Lovers.

## Metadata

- URL: https://medium.com/@mmartinmainan/running-n8n-for-free-on-aws-a-self-hosting-guide-for-n8n-lovers-4e367727f45e
- Author: Martin Maina
- Captured: 2026-10-20T09:30:51+02:00

## Content

![](https://miro.medium.com/v2/resize:fit:1400/format:webp/1*XGULgCOnqP5-SVlAG9YPpA.png)

👋 Hey fellow builder! I recently found myself wanting a production-ready automation platform but didn’t want to pay $20/month for something I barely use (yet). After some trial and error, I managed to get n8n running for free on AWS with proper SSL and a custom domain. Here’s my journey and how you can do it too.

## Why Self-Host n8n? 🤔

n8n is an awesome open-source workflow automation tool (think Zapier/Make but self-hostable). The hosted version starts at $20/month, which is totally fair, but if you’re just starting out or building side projects, that recurring cost adds up. By self-hosting on AWS free tier, you can run it essentially for free for a year, and even after that, an EC2 t2.micro instance is pretty affordable (~$8/month).

## The Architecture at a Glance 🏗️

Here’s what we’re building:

![](https://miro.medium.com/v2/resize:fit:1400/format:webp/1*oK7qeY5ywOITofKAjvkSGA.png)

Think of it as a series of Russian nesting dolls, each handling a specific part of the puzzle:

- AWS EC2 provides the server (free tier eligible!)
- Docker isolates n8n in its own environment
- NGINX acts as your friendly doorman, handling SSL and routing
- Let’s Encrypt gives you free SSL certificates
- DuckDNS gives you a free domain that looks legitimate

## What You’ll Need Before Starting 🧰

- AWS account (with free tier access)
- Basic command line familiarity
- About 30–60 minutes of focused time
- Coffee ☕ (optional but recommended)

## Setting Up Your AWS EC2 Instance 🚀

### First, let’s get our server running:

1. Sign into your AWS Console and navigate to EC2
2. Click “Launch Instance”
3. Name it something memorable like “n8n-automation-server”
4. Choose Amazon Linux 2023 AMI (free tier eligible)
5. Select t2.micro instance type (also free tier eligible)
6. Create a new key pair (or use existing) — **SAVE THIS FILE SECURELY!**
7. For network settings, allow SSH (port 22), HTTP (port 80), and HTTPS (port 443)
8. Launch the instance!

Once your instance is running, note down its public IPv4 address — we’ll need this soon.

## Setting Up a Free Domain with DuckDNS 🦆

Instead of buying a domain, we’ll use DuckDNS for a free subdomain:

1. Go to [DuckDNS.org](https://www.duckdns.org/) and sign in (GitHub, Twitter, etc.)
2. Create a subdomain (e.g., `your-n8n-server.duckdns.org`)
3. Enter your EC2 instance’s public IPv4 address
4. Click “update IP”

Note that DuckDNS domains look totally legit in browsers and work perfectly with SSL certificates!

## Connecting to Your EC2 Instance 💻

Let’s SSH into your fresh server:bash

```cs
# Make your key non-publicly viewable (or SSH will complain)
chmod 400 path/to/your-key.pem# Connect to your instance
ssh -i path/to/your-key.pem ec2-user@your-public-ip
```

You should now be logged into your EC2 instance! Time to set things up.

## Installing Docker and Docker Compose 🐳

First, let’s update the system and install Docker:bash

```cs
# Update system packages
sudo yum update -y
# Install Docker
sudo yum install docker -y
# Start Docker service
sudo systemctl start docker
# Enable Docker to start on boot
sudo systemctl enable docker
# Add your user to Docker group (so you don't need sudo for docker commands)
sudo usermod -aG docker ec2-user
# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
# Make Docker Compose executable
sudo chmod +x /usr/local/bin/docker-compose
```

Important: Log out and back in for the group changes to take effec

```cs
exit
# Then reconnect with your SSH command from earlier
```

## Installing NGINX as a Reverse Proxy 🚦

==NGINX== will be our frontline traffic director:

```cs
# Install NGINX
sudo yum install nginx -y
# Start NGINX
sudo systemctl start nginx
# Enable NGINX to start on boot
sudo systemctl enable nginx
```

At this point, if you visit your EC2 public IP in a browser, you should see the NGINX welcome page!

## Setting Up Your n8n Docker Environment 🛠️

Paste this in your terminal/command prompt:

```cs
# Generate encryption key
ENCRYPTION_KEY=$(openssl rand -base64 24)
echo "Your encryption key is: $ENCRYPTION_KEY"
echo "SAVE THIS SOMEWHERE SAFE!"

# Create docker-compose.yml
cd ~/n8n
tee docker-compose.yml > /dev/null << EOL
version: '3'

services:
  n8n:
    image: n8nio/n8n:latest
    restart: always
    ports:
      - "5678:5678"
    environment:
      - N8N_HOST=customn8naws.duckdns.org
      - N8N_PROTOCOL=https
      - N8N_PORT=443
      - N8N_WEBHOOK_URL= https://your-subdomain.duckdns.org/
      - WEBHOOK_URL=https://your-subdomain.duckdns.org/      
      - NODE_ENV=production
      - N8N_ENCRYPTION_KEY=$ENCRYPTION_KEY
      - N8N_TRUSTED_PROXY_RANGES=0.0.0.0/0
      - N8N_RUNNERS_ENABLED=true
      - N8N_SKIP_WEBHOOK_DEREGISTRATION_SHUTDOWN=true
      - NODE_TLS_REJECT_UNAUTHORIZED=1
    volumes:
      - n8n_data:/home/node/.n8n

volumes:
  n8n_data:
EOL

# Start n8n
sudo docker-compose up -d

# Verify n8n is running
sudo docker-compose ps
```

Important notes:

- Replace `your-subdomain.duckdns.org` with your actual DuckDNS domain

## Getting SSL Certificates with Certbot 🔒

Let’s set up SSL so we don’t get those annoying browser warnings:bash

```cs
# Install Certbot and the NGINX plugin
sudo yum install certbot python3-certbot-nginx -y
# Get your certificate
sudo certbot --nginx -d your-subdomain.duckdns.org
```

Follow the prompts (enter your email, agree to terms, etc.).

Certbot will automatically configure NGINX for you, but we need to make some tweaks…

## Configuring NGINX for n8n 🔧

Let’s create a proper NGINX configuration:

```cs
# Backup the auto-generated config
sudo cp /etc/nginx/conf.d/your-subdomain.duckdns.org.conf /etc/nginx/conf.d/your-subdomain.duckdns.org.conf.bak

# Edit the configuration
sudo nano /etc/nginx/conf.d/your-subdomain.duckdns.org.conf
```

Replace the content with:

```cs
server {
    server_name your-subdomain.duckdns.org;location / {
        proxy_pass http://localhost:5678;
        proxy_set_header Connection '';
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_buffering off;
        proxy_buffer_size 16k;
        proxy_busy_buffers_size 24k;
        proxy_buffers 64 4k;
        chunked_transfer_encoding off;
    }
    # For websocket support (used by n8n editor)
    location /socket.io/ {
        proxy_pass http://localhost:5678/socket.io/;
        proxy_set_header Host $host;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
    listen 443 ssl;
    ssl_certificate /etc/letsencrypt/live/your-subdomain.duckdns.org/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-subdomain.duckdns.org/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;
}
# Redirect HTTP to HTTPS
server {
    if ($host = your-subdomain.duckdns.org) {
        return 301 https://$host$request_uri;
    }
    listen 80;
    server_name your-subdomain.duckdns.org;
    return 404;
}
```

Remember to replace `your-subdomain.duckdns.org` with your actual DuckDNS domain!

## Get Martin Maina’s stories in your inbox

Join Medium for free to get updates from this writer.

Save the file, then test and reload NGINX:

```cs
# Test NGINX configuration
sudo nginx -t
# If successful, reload NGINX
sudo systemctl reload nginx
```

## Starting n8n with Docker Compose 🚀

Now let’s fire up n8n:

```cs
# Navigate to n8n directory
cd ~/n8n
# Start n8n in the background
docker-compose up -d
```

If all went well, you should be able to access n8n by visiting your DuckDNS domain in a browser! 🎉

## Setting Up Initial Authentication 🔐

When you first access n8n, you’ll be prompted to create an admin account. This is super important — don’t skip this step! Creating secure credentials here prevents anyone else from accessing your workflows.

## Common Problems and How to Fix Them 🔧

Throughout my journey setting this up, I encountered several issues that might trip you up too:

### Problem 1: ERR\_SSL\_PROTOCOL\_ERROR

Accessing your n8n instance over HTTPS returns a browser error like:

> This site can’t provide a secure connection  
> ERR\_SSL\_PROTOCOL\_ERROR

### Solution:

SSL termination must happen at NGINX, not in n8n.

Set this in docker-compose.yml:

```cs
environment:
  - N8N_PROTOCOL=http
```

NGINX should proxy requests from HTTPS to [http://localhost:5678](http://localhost:5678/).

```cs
server {
    listen 443 ssl;
    server_name your.domain.com;

    ssl_certificate /etc/letsencrypt/live/your.domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your.domain.com/privkey.pem;

    location / {
        proxy_pass http://localhost:5678;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Problem 2: OAuth Redirect URI Mismatch

If you’re using n8n with services like Google, GitHub, etc., you might see `redirect_uri_mismatch` errors.

### ✅ Solution:

- Ensure `WEBHOOK_URL=https://your-subdomain.duckdns.org/` in your docker-compose.yml (note the trailing slash!)
- When setting up OAuth apps, use `https://your-subdomain.duckdns.org/rest/oauth2-credential/callback` as your redirect URI

### Problem 3: Mismatching Encryption Keys

If you rebuild your container but the data volume persists, you might get cryptic errors.

### ✅ Solution:

- The `/home/node/.n8n` volume retains config including your encryption key
- Always use the same `N8N_ENCRYPTION_KEY` value in your docker-compose.yml
- If you don’t remember your key but have existing data, check the n8n logs to find the key it’s expecting

### Problem 4: Port Conflicts

If you’re running multiple services, you might run into port allocation issues.

Docker fails with:

> *Bind for 0.0.0.0:5678 failed: port is already allocated.*

### ✅ Solution:

- Find what’s using the port:
```cs
sudo lsof -i :5678
```
- Change the port mapping in docker-compose.yml (e.g., from `5678:5678` to `5679:5678`)
```cs
ports:
  - "5678:5678"

ports:
  - "5679:5678"
```
- Update your NGINX config to point to the new port

```cs
version: '3'

services:
  n8n:
    image: n8nio/n8n:latest
    restart: always
    ports:
      - "5678:5678"
    environment:
      - N8N_HOST=your.domain.com
      - N8N_PROTOCOL=http
      - WEBHOOK_URL=https://your.domain.com/
      - NODE_ENV=production
      - N8N_ENCRYPTION_KEY=your-secure-key
      - N8N_TRUSTED_PROXY_RANGES=0.0.0.0/0
    volumes:
      - n8n_data:/home/node/.n8n

volumes:
  n8n_data:
```

## Making Your Setup Resilient 💪

To ensure your n8n instance survives reboots and service disruptions:

1. **Automate container restarts:**
```cs
# Already included in our docker-compose.yml above
restart: always
```

**2\. Set up automatic certificate renewal:**

```cs
# Check if renewal is working
sudo certbot renew --dry-run

# Renewal is handled by a timer/cron job installed by certbot
```

**3\. Back up your data regularly:**

```cs
# Create a backup script
echo '#!/bin/bash
BACKUP_DIR="/home/ec2-user/backups"
mkdir -p $BACKUP_DIR
DATE=$(date +"%Y%m%d-%H%M%S")
tar -czf $BACKUP_DIR/n8n-backup-$DATE.tar.gz -C /home/ec2-user/n8n data
find $BACKUP_DIR -type f -mtime +7 -delete' > ~/backup-n8n.sh

# Make it executable
chmod +x ~/backup-n8n.sh

# Add to crontab
(crontab -l 2>/dev/null; echo "0 2 * * * /home/ec2-user/backup-n8n.sh") | crontab -
```

## Security Considerations 🔒

1. **Change default SSH port** to reduce automated attacks:
```cs
sudo nano /etc/ssh/sshd_config
# Find the line with "Port 22" and change it to something else (e.g., "Port 2222")
sudo systemctl restart sshd
```

Remember to update your AWS security group to allow traffic on the new port!

**2\. Set up a firewall**:

```cs
sudo yum install firewalld -y
sudo systemctl start firewalld
sudo systemctl enable firewalld
sudo firewall-cmd --permanent --add-service=ssh
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

**3\. Use AWS security groups effectively** — only open ports 80, 443, and your SSH port

## Performance Optimization 🚀

The t2.micro instance has limited resources, so here are some tips:

1. **Enable swap space** to prevent out-of-memory issues:
```cs
# Create a 2GB swap file
sudo dd if=/dev/zero of=/swapfile bs=128M count=16
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Make swap persistent
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

**2.Limit n8n resource usage** in your docker-compose.yml:

```cs
services:
  n8n:
    # Add these lines to your existing configuration
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
```

## Limitations of This Setup 🚧

- **AWS Free Tier expires after 12 months** — after that, you’ll pay for EC2 (~$8/month for t2.micro)
- **t2.micro is limited to 1GB RAM** — heavy workflows might struggle
- **SQLite is used by default** — consider upgrading to Postgres for production workloads
- **Webhook reliability** — AWS might change your IP if you stop/start the instance, requiring DuckDNS updates

## Taking It to the Next Level 🔝

If your needs grow, consider these upgrades:

1. **Add a Postgres database** for better performance:
```cs
# Add to your docker-compose.yml
services:
  postgres:
    image: postgres:13
    restart: always
    environment:
      - POSTGRES_USER=n8n
      - POSTGRES_PASSWORD=supersecretpassword
      - POSTGRES_DB=n8n
    volumes:
      - postgres_data:/var/lib/postgresql/data
    
  n8n:
    # Update your n8n service with these environment variables
    environment:
      - DB_TYPE=postgresdb
      - DB_POSTGRESDB_HOST=postgres
      - DB_POSTGRESDB_PORT=5432
      - DB_POSTGRESDB_DATABASE=n8n
      - DB_POSTGRESDB_USER=n8n
      - DB_POSTGRESDB_PASSWORD=supersecretpassword

volumes:
  postgres_data:
```

**2\. Set up auto-updates** for your Docker images: Look into [Watchtower](https://github.com/containrrr/watchtower) to automatically update your containers.

**3\. Purchase a real domain** for a more professional look

## Wrapping Up 🎁

That’s it! You now have a production-ready n8n instance running for free (or very cheap) with proper SSL encryption. Your automated workflows can now run 24/7 without breaking the bank.

Feel free to let me know if I missed anything or if you found a better way to do something. I’m still learning too!

Happy automating! 🤖✨