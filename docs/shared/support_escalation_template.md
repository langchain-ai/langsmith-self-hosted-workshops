# Support Escalation Template

**Use this template when escalating an incident to LangChain Support.**

Copy and fill in each section. Include the diagnostics bundle and any relevant evidence.

---

## Incident Summary

**Start Time:** `YYYY-MM-DD HH:MM:SS UTC`  
**Detection Time:** `YYYY-MM-DD HH:MM:SS UTC`  
**Current Status:** `[Investigating / Escalating / Resolved]`

**Brief Description:**
```
[One-sentence summary of the issue]
```

---

## Symptoms

**Who is impacted:**
- [ ] All users
- [ ] Specific user(s) or workspace(s)
- [ ] Specific endpoints or features
- [ ] Internal operations only

**What's broken:**
- [ ] UI is unreachable or returns errors
- [ ] API endpoints return 5xx errors
- [ ] Traces are missing or delayed
- [ ] Authentication/authorization failures
- [ ] Ingestion is slow or failing
- [ ] Other: `[describe]`

**Error messages observed:**
```
[Paste relevant error messages, redacting any secrets]
```

**User-facing impact:**
```
[Describe what users experience]
```

---

## Recent Changes

**Deployments/Releases:**
- [ ] Helm upgrade/chart change: `[version/date]`
- [ ] Configuration change: `[what changed]`
- [ ] Infrastructure change: `[what changed]`
- [ ] No recent changes

**Timeline:**
```
[Chronological list of changes leading up to the incident]
```

---

## Environment Details

**Cloud Provider:** `[AWS / Azure / GCP / Other]`  
**Region/Location:** `[region]`  
**Kubernetes Service:** `[EKS / AKS / GKE / Other]`  
**Cluster Name:** `[cluster-name]`  
**Namespace:** `[namespace]`

**LangSmith Version:**
- Helm Chart Version: `[version]`
- Image Tags: `[if known]`
- Deployment Method: `[Helm / kubectl / Other]`

**Infrastructure:**
- PostgreSQL: `[RDS / Azure Database / In-cluster / Other]`
- Redis: `[ElastiCache / Azure Cache / In-cluster / Other]`
- ClickHouse: `[Managed / In-cluster]`
- Blob Storage: `[S3 / Azure Blob / GCS / Other]`

---

## Diagnostics Bundle

**Bundle Location:** `[path or URL to diagnostics bundle]`

**Bundle Contents:**
- [ ] Canonical diagnostics script output (`get_k8s_debugging_info.sh`)
- [ ] `kubectl get all -o yaml` snapshot
- [ ] Recent events (`kubectl get events`)
- [ ] Pod logs (API, workers, ClickHouse)
- [ ] Resource usage snapshot (`kubectl top pods/nodes`)
- [ ] Ingress/load balancer configuration
- [ ] Helm values (redacted)

**Bundle Timestamp:** `YYYY-MM-DD HH:MM:SS UTC`

---

## What We've Tried

**Investigation Steps:**
1. `[What you checked and what you found]`
2. `[Next step and result]`
3. `[Continue as needed]`

**Remediation Attempts:**
- [ ] Restarted pods: `[which pods, result]`
- [ ] Checked external service connectivity: `[result]`
- [ ] Verified configuration: `[result]`
- [ ] Other: `[describe]`

**Current Hypothesis:**
```
[Your best guess at the root cause, with evidence]
```

---

## Evidence & Logs

**Key Log Excerpts (redact secrets):**
```
[Paste relevant log lines with timestamps]
```

**Error Patterns:**
```
[Describe patterns you've observed]
```

**Metrics/Signals:**
```
[Any metrics or signals that indicate the issue]
```

---

## Questions for Support

1. `[Your question]`
2. `[Another question]`
3. `[Continue as needed]`

---

## Additional Context

**Related Issues:**
- Previous similar incidents: `[reference]`
- Known limitations: `[describe]`
- Custom configurations: `[describe, redact secrets]`

**Priority:**
- [ ] Critical (service down, all users impacted)
- [ ] High (major feature broken, many users impacted)
- [ ] Medium (degraded performance, some users impacted)
- [ ] Low (minor issue, workaround available)

---

## Next Steps

**What we need from Support:**
- [ ] Root cause analysis
- [ ] Remediation steps
- [ ] Configuration guidance
- [ ] Performance optimization
- [ ] Other: `[describe]`

**Our availability:**
- Timezone: `[timezone]`
- Best time to contact: `[time range]`
- Escalation contact: `[name/email]`

---

**Template Version:** 1.0  
**Last Updated:** `[date]`

**Note:** Always redact secrets, API keys, passwords, and connection strings before sharing. Use `[REDACTED]` or similar markers.

