# BagTrack - Production Management System

A comprehensive web-based piece-rate tracking system for paper bag manufacturing workers, built with Flask and MySQL.

## 🎯 Features

### For Workers
- ✅ Submit production with photo proof
- 📊 Track approved production and payments
- 💰 Confirm payment receipt
- 📜 View complete production history
- 📱 Mobile-first responsive design

### For Admin
- 👥 Manage multiple workers
- ✓ Review and approve/reject submissions
- 💵 Record payments with multiple methods
- 📈 Comprehensive dashboard with statistics
- 🔍 Filter and search production logs
- 👤 Detailed worker profiles
- 📋 Complete audit trail

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- MySQL 5.7+ or MariaDB 10.3+
- pip (Python package manager)

### Installation

1. **Clone or extract the project**
```bash
cd bagtrack
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure MySQL database**

Create the database and user:
```sql
CREATE DATABASE bagtrack_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'bagtrack_user'@'localhost' IDENTIFIED BY 'your_secure_password';
GRANT ALL PRIVILEGES ON bagtrack_db.* TO 'bagtrack_user'@'localhost';
FLUSH PRIVILEGES;
```

Import the schema:
```bash
mysql -u bagtrack_user -p bagtrack_db < schema.sql
```

5. **Configure environment variables**
```bash
cp .env.example .env
# Edit .env with your database credentials
```

Required settings in `.env`:
```
SECRET_KEY=generate-a-random-secret-key
MYSQL_HOST=localhost
MYSQL_USER=bagtrack_user
MYSQL_PASSWORD=your_secure_password
MYSQL_DB=bagtrack_db
```

6. **Run the application**
```bash
python app.py
```

The application will be available at `http://localhost:5000`

### Default Login Credentials

**Admin Account:**
- Phone: 9999999999
- Password: admin123

**Test Worker Account:**
- Phone: 8888888888
- Password: worker123

**⚠️ IMPORTANT: Change these passwords immediately in production!**

## 📱 Usage

### Worker Workflow

1. **Login** with phone number and password
2. **Submit Production**
   - Take photo of produced bags
   - Enter bag type (optional)
   - Enter quantity and rate
   - System calculates total automatically
3. **Track Status**
   - View submission status (Submitted → Approved → Payment Sent → Payment Received)
4. **Confirm Payments**
   - When admin records payment, worker confirms receipt

### Admin Workflow

1. **Review Submissions**
   - View pending submissions on dashboard
   - Click "Review" to see photo and details
   - Approve or reject with reason
2. **Record Payments**
   - Select worker from dropdown
   - Enter payment amount
   - Choose payment method (UPI/Bank/Cash)
   - Add transaction reference and optional screenshot
3. **Monitor Operations**
   - Dashboard shows overall statistics
   - View worker summaries
   - Filter production logs
   - Track payment confirmations

## 🗂️ Database Schema

### Tables

**workers** - User accounts (both admin and workers)
- worker_id, name, phone_number, password_hash, is_admin, is_active

**production** - Production submissions
- production_id, worker_id, photo_path, bag_type, quantity, rate, total_amount, status, rejection_reason

**payments** - Payment records
- payment_id, worker_id, amount, payment_method, transaction_reference, status

**payment_production_links** - Links payments to production entries

**activity_log** - Audit trail of all actions

### Status Flow

Production Status:
1. SUBMITTED (worker submits)
2. APPROVED (admin approves) or REJECTED
3. PAYMENT_SENT (admin records payment)
4. PAYMENT_RECEIVED (worker confirms)

## 🔒 Security Features

- Password hashing using Werkzeug
- Session-based authentication
- Role-based access control (Admin/Worker)
- Input validation and sanitization
- SQL injection protection via parameterized queries
- CSRF protection via Flask sessions
- File upload validation
- Complete audit logging

## 🎨 Design Philosophy

- **Mobile-First**: Optimized for smartphone usage
- **Bold & Industrial**: Distinctive design with Bebas Neue and DM Sans fonts
- **High Contrast**: Dark theme with vibrant orange accents
- **Touch-Friendly**: Large buttons and input fields
- **Fast Loading**: Minimal dependencies, optimized assets

## 📂 Project Structure

```
bagtrack/
├── app.py                 # Main Flask application
├── schema.sql            # Database schema
├── requirements.txt      # Python dependencies
├── .env.example         # Environment variables template
├── templates/           # HTML templates
│   ├── base.html
│   ├── login.html
│   ├── register.html
│   ├── worker_dashboard.html
│   ├── submit_production.html
│   ├── production_history.html
│   ├── admin_dashboard.html
│   ├── review_production.html
│   ├── record_payment.html
│   ├── production_log.html
│   ├── payment_log.html
│   ├── worker_details.html
│   └── error.html
├── static/
│   ├── css/
│   │   └── style.css    # Main stylesheet
│   └── js/
│       └── script.js    # Client-side JavaScript
└── uploads/             # User uploaded files (auto-created)
    ├── production/      # Production photos
    └── payments/        # Payment screenshots
```

## 🔧 Configuration Options

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| SECRET_KEY | Flask secret key | Random generated |
| MYSQL_HOST | MySQL server host | localhost |
| MYSQL_USER | MySQL username | root |
| MYSQL_PASSWORD | MySQL password | (empty) |
| MYSQL_DB | Database name | bagtrack_db |
| UPLOAD_FOLDER | File upload directory | uploads |
| MAX_CONTENT_LENGTH | Max file size (bytes) | 16777216 (16MB) |

### Application Settings

Edit `app.py` to modify:
- Allowed file extensions (images)
- Session timeout
- Upload folder structure

## 📊 API Endpoints

| Endpoint | Method | Access | Description |
|----------|--------|--------|-------------|
| `/` | GET | Public | Landing page |
| `/login` | GET, POST | Public | User login |
| `/logout` | GET | Authenticated | User logout |
| `/register` | GET, POST | Public | Worker registration |
| `/worker/dashboard` | GET | Worker | Worker dashboard |
| `/worker/submit-production` | GET, POST | Worker | Submit production |
| `/worker/production-history` | GET | Worker | View history |
| `/worker/confirm-payment/<id>` | POST | Worker | Confirm payment |
| `/admin/dashboard` | GET | Admin | Admin dashboard |
| `/admin/production-log` | GET | Admin | View all production |
| `/admin/review-production/<id>` | GET, POST | Admin | Review submission |
| `/admin/record-payment` | GET, POST | Admin | Record payment |
| `/admin/payment-log` | GET | Admin | View payments |
| `/admin/worker-details/<id>` | GET | Admin | Worker details |

## 🐛 Troubleshooting

### Database Connection Issues
```bash
# Check MySQL is running
sudo systemctl status mysql

# Test connection
mysql -u bagtrack_user -p bagtrack_db
```

### Upload Directory Permissions
```bash
# Ensure uploads directory is writable
chmod 755 uploads
chmod 755 uploads/production
chmod 755 uploads/payments
```

### Flask Not Starting
```bash
# Check if port 5000 is available
lsof -i :5000

# Use different port
flask run --port 5001
```

## 🚀 Production Deployment

### Using Gunicorn (Recommended)

1. Install Gunicorn:
```bash
pip install gunicorn
```

2. Run with Gunicorn:
```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Using Nginx as Reverse Proxy

Sample Nginx configuration:
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /uploads/ {
        alias /path/to/bagtrack/uploads/;
    }
}
```

### Using systemd Service

Create `/etc/systemd/system/bagtrack.service`:
```ini
[Unit]
Description=BagTrack Production Management System
After=network.target

[Service]
User=www-data
WorkingDirectory=/path/to/bagtrack
Environment="PATH=/path/to/bagtrack/venv/bin"
ExecStart=/path/to/bagtrack/venv/bin/gunicorn -w 4 -b 127.0.0.1:5000 app:app

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable bagtrack
sudo systemctl start bagtrack
```

## 📝 License

This project is provided as-is for manufacturing production tracking purposes.

## 🤝 Support

For issues or questions:
1. Check the troubleshooting section
2. Review error logs in the terminal
3. Check MySQL logs: `/var/log/mysql/error.log`

## 🔄 Updates & Maintenance

### Database Backups
```bash
# Backup database
mysqldump -u bagtrack_user -p bagtrack_db > backup_$(date +%Y%m%d).sql

# Restore database
mysql -u bagtrack_user -p bagtrack_db < backup_20240101.sql
```

### Log Rotation
The activity_log table can grow large. Consider periodic archival:
```sql
-- Archive old logs (older than 6 months)
CREATE TABLE activity_log_archive LIKE activity_log;
INSERT INTO activity_log_archive 
SELECT * FROM activity_log 
WHERE created_at < DATE_SUB(NOW(), INTERVAL 6 MONTH);

DELETE FROM activity_log 
WHERE created_at < DATE_SUB(NOW(), INTERVAL 6 MONTH);
```

---

**Built with ❤️ for efficient production tracking**
