# Access Requests

## Add or verify data bag

1. Check ssh key
1. Check unix groups
1. knife data bag from file users <user>.json

## Chef Access

```
# on chef.gitlab.com
chef-server-ctl user-create <username> <first> <last> <email> $(openssl rand -hex 20)
# copy the output into <username>.pem and drop it in their home directory on deploy
chef-server-ctl org-user-add gitlab <username>
```

## Ops Instance Access

Generally when developers ask for access to the ops instance, we are concerned
with chatops access, which requires developer on `gitlab-com` group.
If access to any other groups are needed, please clarify with the requester.

## Read Only Rails Console Access

When developers ask for access to the rails console, have them submit an access request via Teleport using the [Teleport Rails Console Runbook](../teleport/Connect_to_Rails_Console_via_Teleport.md) - Then approve that request (if appropriate) using the [Teleport Approval Workflow](../teleport/teleport_approval_workflow.md) - If the request is for Read/Write access, it's best to give the commands to an SRE and have them run them.

## Database Access

When developers ask for access to the production database, have them submit an access request via Teleport using the [Teleport Database Runbook](../teleport/Connect_to_Database_Console_via_Teleport.md) - Then approve that request (if appropriate) using the [Teleport Approval Workflow](../teleport/teleport_approval_workflow.md) - If the request is for Read/Write access, it's best to give the commands to an SRE/DBRA and have them run them.
