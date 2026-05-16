# Service Locations

This is a table of various services we run and what they run behind.

| Domain               | Service            | Provider                             |
| -------------------- | ------------------ | ------------------------------------ |
| staging.gitlab.com   | GitLab Web/API/SSH | Cloudflare                           |
| staging.gitlab.com   | static assets      | Cloudflare                           |
| GitLab.com           | GitLab Web/API/SSH | Cloudflare                           |
| GitLab.com           | static assets      | Cloudflare                           |
| ops.GitLab.net       |                    | Cloudflare                           |
| customers.gitlab.com |                    | direct to Azure                      |
| version.gitlab.com   |                    | direct to Google                     |
| pre.gitlab.com       |                    | direct to Google                     |
| about.gitlab.com     |                    | Fronted by Cloudflare, backed by GCS |
