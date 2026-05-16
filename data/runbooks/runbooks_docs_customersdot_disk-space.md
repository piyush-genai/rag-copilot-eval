# Disk space alerts (production)

We have a CRON job that checks the disk space and alerts in `#g_fulfillment_status` if it reaches a threshold:

Currently Slack alerts are triggered when disk space has less than 6% free space (>94% used), and it runs the check every 3 hours.

## What to remove should an alert happen

1. `sudo apt-get clean && sudo apt-get autoremove`
1. Old Nginx logs in `/var/log/nginx`
1. Old production logs in `/home/gitlab-customers/customers-gitlab-com/log`
1. Old Audit logs in `/var/log/audit/`
1. Remove old Frontend assets in `/home/gitlab-customers/customers-gitlab-com/public/packs/` and `/home/gitlab-customers/customers-gitlab-com/public/assets/` (older than 5 days)

For the last point, we should precompile the assets right after removing the files with:

```sh
sudo su gitlab-customers -s /bin/bash
cd ~ && customers-gitlab-com/ && env RAILS_ENV=production NODE_ENV=production ./bin/rails assets:precompile
```

If, at this point, we haven't freed up enough disk space, we can get extra hints using `du` or `ncdu` in the command line.
