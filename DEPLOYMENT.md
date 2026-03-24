# Northflank Deployment Guide

## Prerequisites
- GitHub repository: `shivamaanch/erp-gst-system`
- Northflank account (free tier available)
- PostgreSQL database (Northflank provides managed PostgreSQL)

## Step 1: Create PostgreSQL Database on Northflank

1. Log in to Northflank dashboard
2. Create a new **Addon** → **PostgreSQL**
3. Name: `erp-database`
4. Plan: Choose appropriate plan (Standard or higher recommended)
5. Note the connection string after creation

## Step 2: Deploy the Application

1. Go to **Services** → **Create Service**
2. Select **Combined Service** (Build + Deploy)
3. Configure:
   - **Source**: GitHub
   - **Repository**: `shivamaanch/erp-gst-system`
   - **Branch**: `main`
   - **Build Type**: Dockerfile
   - **Dockerfile Path**: `Dockerfile`

## Step 3: Configure Environment Variables

Add these environment variables in Northflank:

```
SECRET_KEY=<generate-a-long-random-string-here>
DATABASE_URL=${POSTGRESQL_CONNECTION_STRING}
FLASK_ENV=production
FLASK_DEBUG=0
```

To generate SECRET_KEY, run:
```python
python -c "import secrets; print(secrets.token_hex(32))"
```

## Step 4: Link Database to Service

1. In your service settings, go to **Environment**
2. Link the PostgreSQL addon you created
3. The `DATABASE_URL` will be automatically injected

## Step 5: Configure Port

- **Port**: 5000 (matches Dockerfile EXPOSE)
- **Health Check Path**: `/` (optional but recommended)

## Step 6: Deploy

1. Click **Deploy**
2. Wait for build to complete
3. Check logs for any errors

## Step 7: Initialize Database

After first deployment, run migrations:

1. Go to **Jobs** → **Create Job**
2. Use same build image
3. Command: `flask db upgrade`
4. Run once

Or use Northflank shell:
```bash
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

## Step 8: Create Admin User

Run this command in Northflank shell or as a job:

```bash
python -c "
import bcrypt
from app import create_app
from extensions import db
from models import User, Company, FinancialYear
from datetime import date

app = create_app()
with app.app_context():
    company = Company(name='Demo Company', gstin='27AAAAA0000A1Z5', pan='AAAAA0000A', state_code='27')
    db.session.add(company)
    db.session.commit()
    
    fy = FinancialYear(company_id=company.id, year_name='2025-26', start_date=date(2025,4,1), end_date=date(2026,3,31), is_active=True)
    db.session.add(fy)
    db.session.commit()
    
    password_hash = bcrypt.hashpw('admin123'.encode(), bcrypt.gensalt()).decode()
    user = User(company_id=company.id, username='admin', email='admin@demo.com', password_hash=password_hash, role='Admin', is_active=True)
    db.session.add(user)
    db.session.commit()
    print('Admin user created: admin / admin123')
"
```

## Step 9: Access Your Application

Your app will be available at:
```
https://<your-service-name>.northflank.app
```

## Troubleshooting

### Database Connection Issues
- Verify `DATABASE_URL` is correctly set
- Check PostgreSQL addon is running
- Ensure service is linked to database addon

### Build Failures
- Check Dockerfile syntax
- Verify all dependencies in requirements.txt
- Review build logs in Northflank

### Runtime Errors
- Check application logs
- Verify all environment variables are set
- Ensure migrations have run

## Auto-Deploy on Push

Northflank automatically deploys when you push to the `main` branch. To deploy:

```bash
git add .
git commit -m "Your changes"
git push origin main
```

## Scaling

To handle more traffic:
1. Go to **Service Settings** → **Resources**
2. Increase **Replicas** (horizontal scaling)
3. Increase **CPU/Memory** (vertical scaling)

## Monitoring

- **Logs**: Real-time logs in Northflank dashboard
- **Metrics**: CPU, Memory, Network usage
- **Alerts**: Configure alerts for downtime or errors

## Security Checklist

- ✅ Change default admin password immediately
- ✅ Use strong SECRET_KEY
- ✅ Set FLASK_DEBUG=0 in production
- ✅ Enable HTTPS (Northflank provides SSL by default)
- ✅ Regularly update dependencies
- ✅ Backup database regularly

## Cost Optimization

- Use Northflank free tier for testing
- Scale down replicas during low traffic
- Use PostgreSQL connection pooling
- Monitor resource usage

---

**Support**: For issues, check Northflank documentation or contact support.
