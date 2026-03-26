# Live Deployment Checklist

## Before Deployment
- [ ] Backup live database
- [ ] Test deployment on staging server
- [ ] Notify users about downtime

## Deployment Steps
- [ ] Run database migrations
- [ ] Upload new files
- [ ] Restart application
- [ ] Verify all features working

## After Deployment
- [ ] Test login functionality
- [ ] Test company switching
- [ ] Test utilities (backup/restore)
- [ ] Test fixed assets schedule
- [ ] Test chart of accounts
- [ ] Test reports (balance sheet, P&L)
- [ ] Verify all 119 default accounts created

## Rollback Plan
- [ ] Restore database from backup
- [ ] Revert to previous files
- [ ] Restart application
