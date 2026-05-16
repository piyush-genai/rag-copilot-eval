# GCP Quota Analysis - Quick Reference Guide

## Python Script for Monitoring Quota Usage

The script is located at - <https://gitlab.com/gitlab-com/gl-infra/db-migration/-/blob/master/bin/gcs_quota_checker.py>

The script pulls current quota usage vs allocation per project and region.

### Requirements

```bash
pip install google-cloud-compute tabulate
```

### Basic Usage

```bash
# Check staging project in us-east1
python gcp_quota_checker.py --project gitlab-staging-1 --region us-east1

# Check all regions
python gcp_quota_checker.py --project gitlab-staging-1 --all-regions

# Filter SSD quotas only (recommended for your case)
python gcp_quota_checker.py --project gitlab-staging-1 --region us-east1 --filter SSD

# Lower threshold to see more quotas
python gcp_quota_checker.py --project gitlab-staging-1 --region us-east1 --threshold 50

# Export to CSV for analysis
python gcp_quota_checker.py --project gitlab-staging-1 --all-regions --output quotas.csv
```

## Specific Commands for Your Use Case

### 1. Check SSD Quotas Before Upgrade

```bash
# Python version
python gcp_quota_checker.py \
  --project gitlab-staging-1 \
  --region us-east1 \
  --filter "SSD,DISK" \
  --threshold 70 \
  --output ssd_quotas_pre_upgrade.csv
```

### 2. Check N2D Family Quotas

```bash
# Python version
python gcp_quota_checker.py \
  --project gitlab-staging-1 \
  --region us-east1 \
  --filter "N2D,VM_FAMILY"
```

### 3. Comprehensive Pre-Upgrade Check

```bash
# Check all critical quotas across all regions
python gcp_quota_checker.py \
  --project gitlab-staging-1 \
  --all-regions \
  --threshold 60 \
  --output pre_upgrade_audit.csv \
  --show-all
```

## Understanding the Output

### Key Metrics to Watch

For PostgreSQL/Patroni Upgrades:

- `LOCAL_SSD_TOTAL_GB` - Total local SSD across all VMs
- `LOCAL_SSD_TOTAL_GB_PER_VM_FAMILY` - Per VM family (N2D)
- `CPUS` - CPU quota for new instances
- `PERSISTENT_DISK_SSD_GB` - Persistent SSD disks
- `IN_USE_ADDRESSES` - Internal IP addresses
- `INSTANCES` - Total VM instances

### Example Output

```text
⚠️  High Usage Quotas (>= 70%)
================================================================================
Project              Region     Metric                                Usage    Limit   Usage%
gitlab-staging-1     us-east1   LOCAL_SSD_TOTAL_GB                    3600.00  3744.00  96.2%
gitlab-staging-1     us-east1   LOCAL_SSD_TOTAL_GB_N2D                3600.00  3744.00  96.2%
gitlab-staging-1     us-east1   CPUS                                  140.00   200.00   70.0%

Summary:
  Total quotas checked: 156
  High usage quotas (>= 70%): 3
  Critical (>= 90%): 2
  Warning (80-90%): 0

⚠️  SSD-related quotas at risk: 2
  • gitlab-staging-1/us-east1: LOCAL_SSD_TOTAL_GB = 96.2%
  • gitlab-staging-1/us-east1: LOCAL_SSD_TOTAL_GB_N2D = 96.2%
```

## Requesting Quota Increases

If quotas are near limits:

### 1. Via gcloud CLI

```bash
# Request quota increase for LOCAL_SSD_TOTAL_GB
gcloud compute project-info describe \
  --project=gitlab-staging-1 \
  --format="value(quotas.filter(metric:LOCAL_SSD_TOTAL_GB))"

# Submit increase request (need to use Console for this)
# Go to: https://console.cloud.google.com/iam-admin/quotas
```

### 2. Via Console

1. Go to: <https://console.cloud.google.com/iam-admin/quotas>
2. Filter by region: us-east1
3. Filter by metric: LOCAL_SSD_TOTAL_GB
4. Click "EDIT QUOTAS"
5. Request new limit (suggest: +50% above current)

### 3. Calculate Required Quota

```bash
# For Patroni v17 upgrade (4 nodes):
# Current per node: 900 GB local SSD (estimated)
# New nodes needed: 4
# Required: 4 × 900 = 3,600 GB
# Plus existing: 3,600 GB
# Total needed: 7,200 GB (current limit: 3,744 GB)

# Request at least: 8,000 GB to have headroom
```

## Pre-Upgrade Checklist

Run these commands before upgrade:

```bash
# 1. Full quota audit
./gcp_quota_check.sh -p gitlab-staging-1 -a -o pre_upgrade_full.csv

# 2. SSD-specific check
./gcp_quota_check.sh -p gitlab-staging-1 -r us-east1 -f SSD -t 60

# 3. CPU check
./gcp_quota_check.sh -p gitlab-staging-1 -r us-east1 -f CPUS -t 60

# 4. Disk check
./gcp_quota_check.sh -p gitlab-staging-1 -r us-east1 -f DISK -t 60

# 5. IP address check
./gcp_quota_check.sh -p gitlab-staging-1 -r us-east1 -f ADDRESS -t 60
```

## Automating Quota Monitoring

### Cron Job for Daily Checks

```bash
# Add to crontab
0 8 * * * /path/to/gcp_quota_check.sh -p gitlab-staging-1 -t 80 -o /var/log/quotas/daily_$(date +\%Y\%m\%d).csv
```

### Alert on High Usage

```bash
#!/bin/bash
# quota_alert.sh

OUTPUT=$(/path/to/gcp_quota_check.sh -p gitlab-staging-1 -r us-east1 -t 80)
EXIT_CODE=$?

if [[ $EXIT_CODE -ne 0 ]]; then
    echo "$OUTPUT" | mail -s "⚠️ GCP Quota Alert: High Usage Detected" ops@gitlab.com
fi
```

## Troubleshooting

### "Permission Denied" Error

```bash
# Ensure you have compute.regions.get permission
gcloud projects get-iam-policy gitlab-staging-1 \
  --flatten="bindings[].members" \
  --filter="bindings.members:user:$(gcloud config get-value account)"
```

### "Project Not Found" Error

```bash
# List accessible projects
gcloud projects list

# Set active project
gcloud config set project gitlab-staging-1
```

### Quotas Not Updating

```bash
# Clear gcloud cache
gcloud compute regions describe us-east1 \
  --project=gitlab-staging-1 \
  --format=json > /dev/null

# Wait 1-2 minutes and retry
```

## Additional Resources

- [GCP Quotas Documentation](https://cloud.google.com/compute/quotas)
- [Request Quota Increase](https://console.cloud.google.com/iam-admin/quotas)
- [Understanding VM Families](https://cloud.google.com/compute/docs/machine-types)
- [Local SSD Best Practices](https://cloud.google.com/compute/docs/disks/local-ssd)

**Last Updated:** January 2026
**Maintained By:** Database Team
**Version:** 1.0.0
