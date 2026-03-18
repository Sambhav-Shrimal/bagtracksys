# BagTrack Production Deployment Guide

## Prerequisites

- Ubuntu 20.04+ or similar Linux distribution
- Root or sudo access
- Domain name (optional, but recommended)

## Step-by-Step Production Deployment

### 1. System Preparation

Update system packages:
```bash
sudo apt update
sudo apt upgrade -y
```

Install required system packages:
```bash
sudo apt install -y python3 python3-pip python3-venv mysql-server nginx git
sudo apt install -y libmysqlclient-dev python3-dev build-essential
```

### 2. MySQL Setup

Secure MySQL installation:
```bash
sudo mysql_secure_installation
```

Create database and user:
```bash
sudo mysql
```

```sql
CREATE DATABASE bagtrack_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'bagtrack_user'@'localhost' IDENTIFIED BY 'STRONG_PASSWORD_HERE';
GRANT ALL PRIVILEGES ON bagtrack_db.* TO 'bagtrack_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

### 3. Application Setup

Create application user:
```bash
sudo useradd -m -s /bin/bash bagtrack
sudo su - bagtrack
```

Clone/upload application:
```bash
cd /home/bagtrack
# Upload your bagtrack files here or git clone
```

Create virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
```

Install Python dependencies:
```bash
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn
```

### 4. Environment Configuration

Create production environment file:
```bash
nano .env
```

Add configuration:
```
SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_hex(32))')
FLASK_ENV=production
MYSQL_HOST=localhost
MYSQL_USER=bagtrack_user
MYSQL_PASSWORD=STRONG_PASSWORD_HERE
MYSQL_DB=bagtrack_db
```

### 5. Database Initialization

Import schema:
```bash
mysql -u bagtrack_user -p bagtrack_db < schema.sql
```

Update admin password:
```bash
mysql -u bagtrack_user -p bagtrack_db
```

```sql
-- Generate new password hash
-- Use Python: python3 -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('NEW_ADMIN_PASSWORD'))"

UPDATE workers 
SET password_hash = 'GENERATED_HASH_HERE' 
WHERE phone_number = '9999999999';
```

### 6. Create Upload Directories

```bash
mkdir -p uploads/production uploads/payments
chmod 755 uploads uploads/production uploads/payments
```

### 7. Systemd Service Setup

Exit back to sudo user:
```bash
exit
```

Create service file:
```bash
sudo nano /etc/systemd/system/bagtrack.service
```

Add configuration:
```ini
[Unit]
Description=BagTrack Production Management System
After=network.target mysql.service
Requires=mysql.service

[Service]
Type=notify
User=bagtrack
Group=bagtrack
WorkingDirectory=/home/bagtrack
Environment="PATH=/home/bagtrack/venv/bin"
ExecStart=/home/bagtrack/venv/bin/gunicorn \
    --workers 4 \
    --bind 127.0.0.1:5000 \
    --timeout 120 \
    --access-logfile /home/bagtrack/logs/access.log \
    --error-logfile /home/bagtrack/logs/error.log \
    app:app

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Create log directory:
```bash
sudo mkdir -p /home/bagtrack/logs
sudo chown bagtrack:bagtrack /home/bagtrack/logs
```

Enable and start service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable bagtrack
sudo systemctl start bagtrack
sudo systemctl status bagtrack
```

### 8. Nginx Configuration

Create Nginx config:
```bash
sudo nano /etc/nginx/sites-available/bagtrack
```

Add configuration:
```nginx
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;
    
    client_max_body_size 16M;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support (if needed)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
    
    location /uploads/ {
        alias /home/bagtrack/uploads/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    
    location /static/ {
        alias /home/bagtrack/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
```

Enable site:
```bash
sudo ln -s /etc/nginx/sites-available/bagtrack /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 9. SSL/HTTPS Setup (Recommended)

Install Certbot:
```bash
sudo apt install -y certbot python3-certbot-nginx
```

Obtain SSL certificate:
```bash
sudo certbot --nginx -d your-domain.com -d www.your-domain.com
```

Certbot will automatically configure HTTPS and set up auto-renewal.

### 10. Firewall Configuration

```bash
sudo ufw allow 'Nginx Full'
sudo ufw allow OpenSSH
sudo ufw enable
sudo ufw status
```

## Post-Deployment Tasks

### 1. Test the Application

Visit your domain and verify:
- [ ] Login page loads
- [ ] Admin can login
- [ ] Worker can login
- [ ] Production submission works
- [ ] Image upload works
- [ ] Payment recording works

### 2. Change Default Credentials

Login as admin and:
1. Create new admin account with strong password
2. Delete or disable default admin account
3. Delete test worker account

### 3. Setup Backups

Create backup script:
```bash
sudo nano /home/bagtrack/backup.sh
```

```bash
#!/bin/bash
BACKUP_DIR="/home/bagtrack/backups"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Database backup
mysqldump -u bagtrack_user -pPASSWORD bagtrack_db | gzip > $BACKUP_DIR/db_$DATE.sql.gz

# Uploads backup
tar -czf $BACKUP_DIR/uploads_$DATE.tar.gz /home/bagtrack/uploads

# Keep only last 30 days
find $BACKUP_DIR -name "*.gz" -mtime +30 -delete

echo "Backup completed: $DATE"
```

Make executable:
```bash
chmod +x /home/bagtrack/backup.sh
```

Add to crontab for daily backups:
```bash
sudo crontab -e
```

Add line:
```
0 2 * * * /home/bagtrack/backup.sh >> /home/bagtrack/logs/backup.log 2>&1
```

### 4. Setup Monitoring

Install monitoring tools:
```bash
sudo apt install -y htop fail2ban
```

Configure fail2ban for SSH protection:
```bash
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

Monitor application logs:
```bash
# Application logs
sudo journalctl -u bagtrack -f

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# Application logs
tail -f /home/bagtrack/logs/access.log
tail -f /home/bagtrack/logs/error.log
```

## Maintenance Tasks

### Update Application

```bash
sudo su - bagtrack
cd /home/bagtrack

# Backup before update
./backup.sh

# Pull updates
git pull

# Update dependencies
source venv/bin/activate
pip install -r requirements.txt

# Restart service
exit
sudo systemctl restart bagtrack
```

### Database Maintenance

Optimize tables monthly:
```bash
mysql -u bagtrack_user -p bagtrack_db -e "OPTIMIZE TABLE workers, production, payments, payment_production_links, activity_log;"
```

### Log Rotation

Nginx logs are rotated automatically. For application logs:
```bash
sudo nano /etc/logrotate.d/bagtrack
```

```
/home/bagtrack/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 bagtrack bagtrack
    sharedscripts
    postrotate
        systemctl reload bagtrack > /dev/null 2>&1 || true
    endscript
}
```

## Security Checklist

- [ ] Changed all default passwords
- [ ] SSL/HTTPS enabled
- [ ] Firewall configured
- [ ] Fail2ban enabled
- [ ] Regular backups automated
- [ ] MySQL secured (no remote access if not needed)
- [ ] File permissions correct (uploads: 755)
- [ ] Application running as non-root user
- [ ] Environment variables secured
- [ ] Strong SECRET_KEY set

## Troubleshooting

### Application won't start
```bash
# Check service status
sudo systemctl status bagtrack

# Check logs
sudo journalctl -u bagtrack -n 50

# Test Gunicorn directly
sudo su - bagtrack
cd /home/bagtrack
source venv/bin/activate
gunicorn -b 127.0.0.1:5000 app:app
```

### Database connection issues
```bash
# Test MySQL connection
mysql -u bagtrack_user -p bagtrack_db

# Check MySQL is running
sudo systemctl status mysql
```

### Nginx issues
```bash
# Test configuration
sudo nginx -t

# Check logs
sudo tail -f /var/log/nginx/error.log
```

### Upload issues
```bash
# Check permissions
ls -la /home/bagtrack/uploads/

# Fix permissions
sudo chown -R bagtrack:bagtrack /home/bagtrack/uploads/
chmod -R 755 /home/bagtrack/uploads/
```

## Performance Tuning

### Gunicorn Workers

Calculate optimal workers:
```
workers = (2 × CPU_cores) + 1
```

Update in systemd service file.

### MySQL Optimization

Edit `/etc/mysql/mysql.conf.d/mysqld.cnf`:
```
[mysqld]
innodb_buffer_pool_size = 256M
max_connections = 100
query_cache_size = 32M
```

Restart MySQL:
```bash
sudo systemctl restart mysql
```

### Nginx Caching

Add to Nginx config for better performance:
```nginx
proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=my_cache:10m max_size=1g inactive=60m;

location / {
    proxy_cache my_cache;
    proxy_cache_valid 200 1h;
    # ... other proxy settings
}
```

## Scaling Considerations

For higher loads:
- Increase Gunicorn workers
- Use connection pooling for MySQL
- Implement Redis for session storage
- Use CDN for static assets
- Consider load balancer for multiple instances

---

**Deployment Date:** _________________
**Deployed By:** _________________
**Domain:** _________________
**Server IP:** _________________
