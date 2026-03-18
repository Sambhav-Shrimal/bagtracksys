# 🚀 BagTrack - 5-Minute Setup Guide

## Step 1: Prerequisites Check

✅ **You Need:**
- Python 3.8 or higher
- MySQL 5.7 or higher
- A terminal/command prompt

✅ **Quick Check:**
```bash
python3 --version   # Should show 3.8+
mysql --version     # Should show 5.7+
```

---

## Step 2: Database Setup (3 minutes)

### A. Create Database

Open MySQL:
```bash
mysql -u root -p
```

Run these commands (copy-paste all):
```sql
CREATE DATABASE bagtrack_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'bagtrack_user'@'localhost' IDENTIFIED BY 'BagTrack@2024';
GRANT ALL PRIVILEGES ON bagtrack_db.* TO 'bagtrack_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

### B. Import Schema

```bash
cd bagtrack
mysql -u bagtrack_user -pBagTrack@2024 bagtrack_db < schema.sql
```

✅ **Verify:**
```bash
mysql -u bagtrack_user -pBagTrack@2024 bagtrack_db -e "SHOW TABLES;"
```
You should see 5 tables.

---

## Step 3: Application Setup (2 minutes)

### Run Setup Script:

**On Linux/Mac:**
```bash
chmod +x start.sh
./start.sh
```

**On Windows:**
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

### Edit .env file:

Open `.env` and update:
```
SECRET_KEY=your-random-secret-here-change-this
MYSQL_PASSWORD=BagTrack@2024
```

**Generate SECRET_KEY:**
```bash
python3 -c 'import secrets; print(secrets.token_hex(32))'
```

---

## Step 4: Launch! (30 seconds)

```bash
python app.py
```

You should see:
```
 * Running on http://127.0.0.1:5000
```

Open your browser: **http://localhost:5000**

---

## Step 5: Login & Test

### 👨‍💼 Admin Login:
- Phone: **9999999999**
- Password: **admin123**

### 👷 Worker Login:
- Phone: **8888888888**
- Password: **worker123**

---

## 🎯 First Actions

### As Worker:
1. Click "Submit Production"
2. Take/upload a photo
3. Enter quantity and rate
4. Submit

### As Admin:
1. Go to Admin Dashboard
2. See pending submission
3. Click "Review"
4. Approve it
5. Go to "Record Payment"
6. Pay the worker

### Back as Worker:
1. See payment notification
2. Confirm payment received
3. Check your history

---

## ⚠️ Troubleshooting

### "Can't connect to MySQL"
```bash
# Check MySQL is running
sudo systemctl status mysql
# or
brew services list | grep mysql
```

### "Module not found"
```bash
# Make sure virtual environment is activated
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Reinstall dependencies
pip install -r requirements.txt
```

### "Permission denied" on uploads
```bash
mkdir -p uploads/production uploads/payments
chmod 755 uploads uploads/production uploads/payments
```

### Port 5000 already in use
```bash
# Find what's using it
lsof -i :5000

# Or use different port
flask run --port 5001
```

---

## 📱 Access from Phone

1. Find your computer's IP:
   ```bash
   # Linux/Mac
   ifconfig | grep "inet "
   # Windows
   ipconfig
   ```

2. Run app on all interfaces:
   ```bash
   flask run --host=0.0.0.0
   ```

3. On phone, visit:
   ```
   http://YOUR_IP:5000
   ```

---

## 🔒 IMPORTANT - Change Passwords!

Once you verify it works:

```bash
mysql -u bagtrack_user -p bagtrack_db
```

```sql
-- Generate hash in Python first:
-- python3 -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('YOUR_NEW_PASSWORD'))"

UPDATE workers 
SET password_hash = 'YOUR_GENERATED_HASH' 
WHERE phone_number = '9999999999';
```

---

## 🎉 Success Checklist

- [ ] Database created and schema imported
- [ ] Application starts without errors
- [ ] Can login as admin
- [ ] Can login as worker
- [ ] Worker can submit production
- [ ] Admin can review submission
- [ ] Admin can record payment
- [ ] Worker can confirm payment
- [ ] Photos upload successfully

---

## 📚 Next Steps

### Learn More:
- **README.md** - Full user guide
- **ARCHITECTURE.md** - How it works
- **DEPLOYMENT.md** - Production setup

### Customize:
- Colors in `static/css/style.css`
- Add bag types in templates
- Modify workflows in `app.py`

### Deploy:
- Follow **DEPLOYMENT.md** for production
- Set up SSL/HTTPS
- Configure backups
- Set up monitoring

---

## 💬 Quick Reference

### Start Application:
```bash
source venv/bin/activate
python app.py
```

### Stop Application:
Press `Ctrl + C`

### View Logs:
Watch terminal output

### Backup Database:
```bash
mysqldump -u bagtrack_user -p bagtrack_db > backup.sql
```

### Reset Demo Data:
```bash
mysql -u bagtrack_user -p bagtrack_db < schema.sql
```

---

## 🏁 You're Ready!

The system is now running and ready for production tracking.

**Need Help?**
- Check README.md for detailed documentation
- Review error messages in terminal
- Check MySQL error logs
- Verify file permissions on uploads/

**Happy Tracking! 📦**
