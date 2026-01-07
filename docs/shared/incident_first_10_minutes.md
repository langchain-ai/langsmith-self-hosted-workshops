# First 10 Minutes: Incident Response Checklist

**When:** You detect or are alerted to a LangSmith self-hosted issue.

**Goal:** Collect evidence, stabilize if possible, and prepare for escalation—without making things worse.

---

## ⚠️ Critical: Do NOT Redeploy

**Resist the urge to:**
- Run `helm upgrade` or `kubectl rollout restart`
- Delete pods "to see if they come back"
- Scale resources up/down
- Change configuration

**Why:** Redeploying destroys evidence and may mask the root cause. Collect diagnostics first.

---

## Minute 0-2: Triage & Scope

- [ ] **Confirm the issue:** What's broken? (UI down, API 5xx, traces missing, auth failing)
- [ ] **Check who's impacted:** All users, specific endpoints, specific features?
- [ ] **Note the time:** Record detection time and any recent changes (deployments, config changes, infrastructure changes)
- [ ] **Check basic connectivity:**
  ```bash
  kubectl cluster-info
  kubectl get nodes
  kubectl get pods -n <namespace>
  ```

---

## Minute 2-5: Quick Health Check

- [ ] **Pod status:**
  ```bash
  kubectl get pods -n <namespace> -o wide
  ```
  Look for: CrashLoopBackOff, Pending, Error states

- [ ] **Recent events:**
  ```bash
  kubectl get events -n <namespace> --sort-by='.lastTimestamp' | tail -20
  ```
  Look for: Failed scheduling, image pull errors, resource limits

- [ ] **Ingress/Load Balancer:**
  ```bash
  kubectl get ingress -n <namespace>
  ```
  Check if endpoint is reachable (curl or browser)

- [ ] **Key deployments:**
  ```bash
  kubectl get deployments -n <namespace>
  kubectl describe deployment <deployment-name> -n <namespace>
  ```

---

## Minute 5-8: Collect Diagnostics Bundle

- [ ] **Run canonical diagnostics script:**
  ```bash
  # Download and run the official script
  curl -O https://raw.githubusercontent.com/langchain-ai/helm/main/charts/langsmith/scripts/get_k8s_debugging_info.sh
  chmod +x get_k8s_debugging_info.sh
  ./get_k8s_debugging_info.sh <namespace>
  ```
  This captures: pod logs, events, resource usage, configuration

- [ ] **Save timestamped snapshot:**
  ```bash
  TIMESTAMP=$(date +%Y%m%d-%H%M%S)
  mkdir -p artifacts/incident-$TIMESTAMP
  
  kubectl get all -n <namespace> -o yaml > artifacts/incident-$TIMESTAMP/all-resources.yaml
  kubectl get events -n <namespace> --sort-by='.lastTimestamp' > artifacts/incident-$TIMESTAMP/events.txt
  ```

- [ ] **Check logs for obvious errors:**
  ```bash
  # Check API server logs
  kubectl logs -n <namespace> -l app=langsmith-api --tail=100
  
  # Check worker logs
  kubectl logs -n <namespace> -l app=langsmith-worker --tail=100
  ```
  Look for: connection errors, timeouts, authentication failures, resource exhaustion

---

## Minute 8-10: Identify Likely Root Cause

Based on symptoms, check the most likely culprits:

### If UI/API is down:
- [ ] Check ingress/load balancer status (via cloud helper or kubectl)
- [ ] Check API pod logs for startup errors
- [ ] Verify external services (PostgreSQL, Redis) are reachable

### If traces are missing/delayed:
- [ ] Check ClickHouse connectivity and logs
- [ ] Check worker pod logs for insert errors
- [ ] Verify blob storage configuration (if large payloads)

### If authentication fails:
- [ ] Check OIDC/SAML configuration (Module 2 validation)
- [ ] Check IdP connectivity
- [ ] Review auth-related pod logs

### If ingestion is slow:
- [ ] Check Redis connectivity and latency
- [ ] Check worker pod resource usage
- [ ] Look for queue backlogs

---

## After 10 Minutes: Decision Point

**If you've identified and can safely fix the issue:**
- Document what you changed
- Verify recovery
- Collect post-recovery diagnostics

**If you need help:**
- Use the [Support Escalation Template](../shared/support_escalation_template.md)
- Include the diagnostics bundle
- Note what you've tried and the results

**If the issue is critical and escalating:**
- Continue collecting evidence every 5-10 minutes
- Document timeline of symptoms
- Prepare escalation with all evidence

---

## What NOT to Do

- ❌ Don't delete namespaces or persistent volumes
- ❌ Don't change database passwords or connection strings
- ❌ Don't scale resources without understanding the bottleneck
- ❌ Don't ignore error messages—they're evidence
- ❌ Don't skip the diagnostics bundle—Support will ask for it

---

## Quick Reference: Common Failure Patterns

| Symptom | Likely Cause | First Check |
|---------|--------------|-------------|
| All pods CrashLoopBackOff | Config error, missing secret | `kubectl describe pod` |
| API 5xx errors | Database/Redis connection | Pod logs, service endpoints |
| Traces not appearing | ClickHouse connectivity | ClickHouse pod logs |
| Slow ingestion | Redis latency, worker backlog | Worker logs, Redis metrics |
| Auth redirect loop | OIDC/SAML misconfiguration | Auth pod logs, IdP connectivity |

---

**Remember:** The goal is evidence collection and safe triage, not immediate resolution. A good diagnostics bundle is worth more than a hasty fix.

