# Cloudflare Audit Log Rule Processing

The following flow chart describes the processing performed on every rule
when [Cloudflare Audit Log](https://ops.gitlab.net/gitlab-com/gl-infra/cloudflare-audit-log) runs.

```mermaid
graph TD

Rule{Rule description} ==> Parsed[full description could be parsed and is valid]
Rule ==> NotParsed[description cannot be parsed]
Rule ==> IssueID[only the issue ID could be extracted & is valid]

Parsed --> Duration{rule duration}
NotParsed --> AbortProcessing[rule processing aborted]
IssueID --> CommentWithErrors[leave issue comment with error details]

CommentWithErrors --> AbortProcessing
AbortProcessing --> END{end}

Duration ==> LongTerm[long-term]
LongTerm --> NoteLongTerm[prepare label `role-duration::long-term`]
NoteLongTerm --> ApplyLabels

Duration ==> Temporary[temporary]
Temporary --> NoteTemporary[prepare label `role-duration::temporary`]
NoteTemporary --> MaxLifetime{maximum lifetime in h}

MaxLifetime ==> Set[explicitly set]
MaxLifetime ==> Unset[unset/automatic]

Set --> IsMaxExpired{has elapsed?}
IsMaxExpired ==> MaxExpired[yes] --> Expired[has expired]
IsMaxExpired ==> MaxNotExpired[no] --> MinLifetime{minimum lifetime in h}
NotExpired -->  ApplyLabels

Unset --> MinLifetime
MinLifetime ==> MinSet[set, check for value]
MinLifetime ==> MinUnset[unset, check for 48h]
MinUnset --> MinElapsed{has elapsed}
MinSet --> MinElapsed{has elapsed}
MinElapsed ==> HasElapsed[yes]
MinElapsed ==> HasNotElapsed[no]

HasNotElapsed --> NotExpired[not expired]
HasElapsed --> CheckTraffic[Check traffic in last 24h]

CheckTraffic --> NoteTraffic[add the traffic level to the issue comment about to be posted]

NoteTraffic --> ReqCount{> 0 reqests?}
ReqCount ==> MoreRequests[yes] --> NotExpired
ReqCount ==> NoRequests[no] --> Expired

Expired --> Delete[delete rule in Cloudflare]
Delete --> OnError[On error add to the message of the comment about to be posted]
OnError --> ApplyLabels

subgraph choose and apply labels
ApplyLabels[evaluate rule filter and select candidate labels for `rule-filter`] --> EvaluateType{rule type}
EvaluateType ==> TypeBypass['bypass']
EvaluateType ==> TypeOther[other]

TypeBypass --> EvaluateBlock[determine matching `bypass-action` labels/firewall `products`]

EvaluateBlock --> RenderComment[render comment before posting - implicit label check]
TypeOther --> RenderComment

RenderComment --> MatchComment{matches previous}
MatchComment ==> CommentMatch[yes]
MatchComment ==> CommentNotMatch[no]

CommentNotMatch --> Comment[comment status on issue & apply labels]
end

CommentMatch --> END
Comment --> END

subgraph expiry detection
MaxLifetime
Set
IsMaxExpired
MaxNotExpired
MaxExpired
Expired
NotExpired
Unset
MinLifetime
MinSet
MinUnset
MinElapsed
HasElapsed
HasNotElapsed
CheckTraffic
NoteTraffic
ReqCount
MoreRequests
NoRequests
end
```
