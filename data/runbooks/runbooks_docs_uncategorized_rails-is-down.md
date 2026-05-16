# Rails is down

Many data gathering exercises listed in these docs involve accessing the Rails console.

However, during particularly severe incidents, the Rails console may be totally inaccessible, likely because Redis (specifically `redis-cache`) is unusable. This would also render Teleport useless as it uses the Rails console.

## Alternative methods of data access

In the absence of the Rails console, you have a few choices:

* The Patroni console does not rely on Redis, so you can use the Patroni nodes to run SQL queries against the database via `sudo gitlab-psql`
  * **Be aware that you will be running queries against live data if you use this option!**
* If the data you're collecting doesn't necessarily need to be up-to-date, you can also run SQL queries against the delayed replica instances (`postgres-dr-main-delayed-*`, `postgres-ci-dr-delayed-* ` et al.)
* You can create a clone of the production database in the [Database Lab Platform](https://console.postgres.ai/), [access its console manually](https://docs.gitlab.com/ee/development/database/database_lab.html#manual-access-through-the-postgresai-instances-page) and run queries. However you will need to have set up the requisite access (`AllFeaturesUser`) beforehand
* If the API is working and you happen to have a [personal access token](https://docs.gitlab.com/ee/user/profile/personal_access_tokens.html) handy (it will likely need to have admin access rights for privileged operations), you can try [querying the API](https://docs.gitlab.com/ee/api/api_resources.html)
* There _may_ be a [dashboard in the Data Warehouse](https://app.periscopedata.com/app/gitlab/910238/GitLab-Dashboard-Index) that provides you with a view of the data needed
