# BagTrack System Architecture

## Overview

BagTrack is a production-grade web application for managing piece-rate paper bag production workers. It provides a complete workflow from production submission to payment confirmation with full audit trails.

## Technology Stack

### Backend
- **Framework**: Flask 3.0 (Python)
- **Database**: MySQL 5.7+ / MariaDB 10.3+
- **Authentication**: Werkzeug password hashing, Flask sessions
- **File Handling**: Werkzeug secure file uploads

### Frontend
- **Template Engine**: Jinja2
- **CSS**: Custom CSS with CSS Variables
- **JavaScript**: Vanilla ES6+
- **Fonts**: Bebas Neue (display), DM Sans (body) from Google Fonts

### Deployment
- **WSGI Server**: Gunicorn
- **Web Server**: Nginx (reverse proxy)
- **Process Manager**: systemd
- **SSL/TLS**: Let's Encrypt (Certbot)

## System Architecture Diagram

```
┌─────────────┐
│   Browser   │ (Mobile/Desktop)
└──────┬──────┘
       │ HTTPS
       ↓
┌─────────────┐
│    Nginx    │ (Reverse Proxy, Static Files, SSL)
└──────┬──────┘
       │ HTTP
       ↓
┌─────────────┐
│  Gunicorn   │ (WSGI Server, 4 workers)
└──────┬──────┘
       │
       ↓
┌─────────────┐
│ Flask App   │ (Application Logic)
└──────┬──────┘
       │
       ├──────→ MySQL (Data Storage)
       └──────→ File System (Image Uploads)
```

## Database Architecture

### Entity Relationship Diagram

```
┌─────────────────┐
│     workers     │
│─────────────────│
│ worker_id (PK)  │
│ name            │
│ phone_number    │◄────┐
│ password_hash   │     │
│ is_admin        │     │
│ is_active       │     │
└─────────────────┘     │
         │              │
         │ 1:N          │
         ↓              │
┌─────────────────┐     │
│   production    │     │
│─────────────────│     │
│ production_id   │     │
│ worker_id (FK)  │─────┘
│ photo_path      │
│ bag_type        │
│ quantity        │
│ rate            │
│ total_amount    │
│ status          │
│ rejection_reason│
│ reviewed_by (FK)│
└────────┬────────┘
         │ N:M
         ↓
┌────────────────────────┐
│ payment_production_links│
│────────────────────────│
│ link_id (PK)           │
│ payment_id (FK)        │
│ production_id (FK)     │
│ amount_allocated       │
└────────┬───────────────┘
         │
         ↓
┌─────────────────┐
│    payments     │
│─────────────────│
│ payment_id (PK) │
│ worker_id (FK)  │
│ amount          │
│ payment_method  │
│ status          │
│ paid_by (FK)    │
└─────────────────┘

┌─────────────────┐
│  activity_log   │
│─────────────────│
│ log_id (PK)     │
│ user_id (FK)    │
│ action          │
│ entity_type     │
│ entity_id       │
│ details         │
│ ip_address      │
│ created_at      │
└─────────────────┘
```

## Application Architecture

### MVC Pattern

```
┌──────────────────────────────────────────┐
│              PRESENTATION                │
│  ┌────────┐  ┌────────┐  ┌────────┐    │
│  │ Base   │  │Worker  │  │ Admin  │    │
│  │Template│  │Templates│ │Templates│   │
│  └────────┘  └────────┘  └────────┘    │
└──────────────────────────────────────────┘
                    ↕
┌──────────────────────────────────────────┐
│               CONTROLLER                 │
│  ┌────────────────────────────────────┐ │
│  │         Flask Routes               │ │
│  │  - Authentication                  │ │
│  │  - Worker Routes                   │ │
│  │  - Admin Routes                    │ │
│  │  - API Routes                      │ │
│  └────────────────────────────────────┘ │
└──────────────────────────────────────────┘
                    ↕
┌──────────────────────────────────────────┐
│                 MODEL                    │
│  ┌────────────────────────────────────┐ │
│  │        MySQL Database              │ │
│  │  - workers                         │ │
│  │  - production                      │ │
│  │  - payments                        │ │
│  │  - payment_production_links        │ │
│  │  - activity_log                    │ │
│  └────────────────────────────────────┘ │
└──────────────────────────────────────────┘
```

## Request Flow

### Worker Production Submission

```
User → Login → Worker Dashboard → Submit Production

1. User fills form + uploads photo
2. Client validates input
3. POST /worker/submit-production
4. Flask receives request
5. Validates file type and size
6. Generates unique filename
7. Saves file to uploads/production/
8. Calculates total_amount
9. Inserts record into production table
10. Logs activity
11. Commits transaction
12. Flash success message
13. Redirects to dashboard
```

### Admin Review Process

```
Admin → Production Log → Review Submission

1. Admin clicks Review
2. GET /admin/review-production/<id>
3. Flask queries production + worker data
4. Renders review template with photo
5. Admin approves/rejects
6. POST /admin/review-production/<id>
7. Updates production status
8. If approved: status → APPROVED
9. If rejected: status → REJECTED + reason
10. Updates reviewed_by and reviewed_at
11. Logs activity
12. Commits transaction
13. Redirects to dashboard
```

### Payment Flow

```
Admin → Record Payment → Worker → Confirm Payment

Admin Side:
1. GET /admin/record-payment
2. Select worker from dropdown
3. Enter amount, method, reference
4. Optional: Upload screenshot
5. POST /admin/record-payment
6. Insert payment record
7. Link to approved productions
8. Update production status → PAYMENT_SENT
9. Flash success message

Worker Side:
10. Worker sees pending payment on dashboard
11. POST /worker/confirm-payment/<id>
12. Update payment status → PAYMENT_RECEIVED
13. Update linked productions → PAYMENT_RECEIVED
14. Log confirmation
15. Flash success message
```

## Security Architecture

### Authentication Flow

```
1. User submits phone + password
2. Query workers table
3. Verify user exists and is_active
4. Check password using check_password_hash()
5. Create session with user_id, name, is_admin
6. Session cookie sent to client (HttpOnly)
7. Subsequent requests include session cookie
8. @login_required decorator verifies session
9. @admin_required checks is_admin flag
```

### Security Layers

1. **Input Validation**
   - Client-side: HTML5 validation, JavaScript checks
   - Server-side: Type checking, range validation

2. **SQL Injection Prevention**
   - Parameterized queries (MySQLdb)
   - No string concatenation in SQL

3. **File Upload Security**
   - Whitelist allowed extensions
   - Secure filename sanitization
   - File size limits (16MB)
   - Separate upload directories

4. **Session Security**
   - Secure random SECRET_KEY
   - HttpOnly cookies
   - Session timeout

5. **Access Control**
   - Role-based (Admin/Worker)
   - Route-level decorators
   - Resource ownership checks

6. **Audit Trail**
   - All actions logged to activity_log
   - IP address captured
   - Immutable log records

## File Storage Architecture

```
uploads/
├── production/
│   ├── {worker_id}_{timestamp}_{filename}.jpg
│   └── ...
└── payments/
    ├── payment_{worker_id}_{timestamp}_{filename}.jpg
    └── ...

Naming Convention:
- Includes worker_id for tracking
- Timestamp prevents collisions
- Original filename for reference
- Secured with secure_filename()
```

## State Management

### Production Status States

```
SUBMITTED
    ↓
APPROVED or REJECTED
    ↓
PAYMENT_SENT (only if APPROVED)
    ↓
PAYMENT_RECEIVED
```

### Payment Status States

```
PAYMENT_SENT
    ↓
PAYMENT_RECEIVED
```

## API Routes Architecture

### Public Routes
- `GET /` - Landing page
- `GET,POST /login` - Authentication
- `GET,POST /register` - Worker registration

### Worker Routes (Authenticated)
- `GET /worker/dashboard` - Main dashboard
- `GET,POST /worker/submit-production` - Submit production
- `GET /worker/production-history` - View history
- `POST /worker/confirm-payment/<id>` - Confirm payment

### Admin Routes (Admin Only)
- `GET /admin/dashboard` - Admin dashboard
- `GET /admin/production-log` - All productions
- `GET,POST /admin/review-production/<id>` - Review submission
- `GET,POST /admin/record-payment` - Record payment
- `GET /admin/payment-log` - Payment history
- `GET /admin/worker-details/<id>` - Worker details

### Utility Routes
- `GET /uploads/<path>` - Serve uploaded files
- `GET /api/worker-pending/<id>` - Get worker pending amount

## Performance Considerations

### Database Optimizations
- Indexed columns: worker_id, status, submitted_at, phone_number
- Foreign key constraints for data integrity
- InnoDB engine for ACID compliance

### Caching Strategy
- Static files: Nginx serves directly
- Images: Browser cache headers
- No application-level caching (real-time data required)

### Scalability
- Stateless application design
- Horizontal scaling possible with:
  - Load balancer
  - Shared file storage (NFS/S3)
  - Database replication

## Monitoring Points

### Application Health
- Gunicorn worker status
- Database connection pool
- Response times
- Error rates

### System Resources
- CPU usage
- Memory usage
- Disk space (uploads folder)
- Database size

### Business Metrics
- Daily submissions
- Approval rates
- Payment completion rates
- Active workers

## Backup Strategy

### What to Backup
1. MySQL database (daily)
2. Uploads folder (daily)
3. Application code (version control)
4. Configuration files (.env)

### Backup Retention
- Daily: 30 days
- Weekly: 12 weeks
- Monthly: 12 months

## Disaster Recovery

### RTO (Recovery Time Objective): 4 hours
### RPO (Recovery Point Objective): 24 hours

Recovery Steps:
1. Restore MySQL from latest backup
2. Restore uploads folder
3. Deploy application code
4. Update .env configuration
5. Restart services
6. Verify functionality

## Future Enhancements

### Potential Features
- SMS notifications for status updates
- Mobile app (React Native)
- Batch payment processing
- Analytics dashboard
- Export to Excel/PDF
- Multi-language support
- API for third-party integrations

### Technical Improvements
- Redis for session storage
- Celery for background tasks
- Elasticsearch for full-text search
- Docker containerization
- CI/CD pipeline
- Automated testing suite

---

**Document Version:** 1.0  
**Last Updated:** 2024  
**Architecture Review:** Recommended quarterly
