# Module 4: Troubleshooting & Incident Response

**Goal:** Teach operators how to diagnose LangSmith self-hosted issues under pressure, collect the right evidence, and resolve incidents efficiently—either independently or with LangChain Support.

**Duration:** ~3-4 hours (with optional full incident drill)  
**Audience:** On-call engineers, platform owners, SREs, and anyone responsible for keeping LangSmith healthy  
**Prerequisites:**
- Module 1 complete: LangSmith deployed and reachable
- Module 2 complete: Authentication configured
- Module 3 complete: Production operations concepts understood
- Participants own day-2 operations

---

## Overview

Module 4 is hands-on: learners will introduce subtle but noticeable failures and debug them using standard tools and the canonical diagnostics bundle. This module builds the muscle memory needed for real incidents.

**What you'll accomplish:**
- Understand common failure modes and their symptoms
- Master the "first 10 minutes" incident response checklist
- Learn to collect canonical diagnostics bundles
- Practice debugging with guided failure labs
- Know when and how to escalate to Support

**What this module avoids:**
- Deep dives into specific monitoring tools (assumes basic kubectl/helm)
- Performance optimization (covered in Module 3)
- Infrastructure provisioning (covered in Module 1)
- Authentication configuration (covered in Module 2)

---

## Section 1: Incident Reality Check

### The Mindset

**Incidents happen.** Even with perfect configuration, production systems fail. The difference between a 30-minute incident and a 4-hour outage is often preparation and process.

**Key principles:**
1. **Collect evidence first.** Don't redeploy, restart, or reconfigure until you understand what's wrong.
2. **Time is evidence.** Every minute that passes without collecting diagnostics is lost information.
3. **Symptoms are clues.** The same root cause can manifest differently depending on load, timing, and configuration.
4. **Support needs context.** A good diagnostics bundle is worth more than a perfect description.

### What Makes Incidents Hard

**Pressure:**
- Users are impacted
- Management is asking for updates
- You're on-call and tired
- Multiple systems are involved

**Complexity:**
- Distributed systems have many moving parts
- Failures cascade (one service fails, others follow)
- Symptoms don't always point to root cause
- Configuration drift accumulates over time

**Tooling:**
- Too many tools (which one shows the truth?)
- Too few tools (missing critical information)
- Tools that hide the problem (aggregation, sampling)

**This module prepares you for all of these.**

---

## Section 2: Common Failure Modes

### Ingestion & Tracing Failures

**Symptoms:**
- Traces appear delayed or missing
- Worker pods show errors in logs
- ClickHouse insert errors
- Queue backlogs

**Common causes:**
- ClickHouse connectivity issues (network, credentials, resource limits)
- Blob storage misconfiguration (large payloads fail)
- Worker resource exhaustion (CPU/memory limits)
- Redis connectivity (job queue backing up)

**What to check first:**
- Worker pod logs
- ClickHouse pod status and logs
- Redis connectivity and latency
- Blob storage configuration

### UI & API Failures

**Symptoms:**
- UI returns 5xx errors
- API endpoints timeout
- Login fails or redirects loop
- Specific features don't work

**Common causes:**
- Database connectivity (PostgreSQL unreachable)
- Authentication misconfiguration (OIDC/SAML)
- Ingress/load balancer issues
- API pod crashes or resource limits

**What to check first:**
- API pod logs
- Database connectivity
- Ingress status and configuration
- Authentication configuration (Module 2 validation)

### Authentication Failures

**Symptoms:**
- Users can't log in
- Redirect loops
- 403 errors after successful login
- Session timeouts

**Common causes:**
- IdP connectivity issues
- OIDC/SAML configuration drift
- Secret rotation without updating LangSmith
- Network policies blocking egress

**What to check first:**
- Auth pod logs
- IdP connectivity (curl to issuer URL)
- OIDC/SAML configuration (Module 2 validation)
- Network policies

---

## Section 3: First 10 Minutes Checklist

**The first 10 minutes of an incident are critical.** This is when you collect the most valuable evidence and make decisions that determine how long the incident lasts.

### What NOT to Do

**Resist the urge to:**
- Run `helm upgrade` or `kubectl rollout restart`
- Delete pods "to see if they come back"
- Scale resources up/down
- Change configuration

**Why:** Redeploying destroys evidence and may mask the root cause. Collect diagnostics first.

### The Checklist

See [First 10 Minutes Checklist](../shared/incident_first_10_minutes.md) for the complete reference.

**Quick summary:**
1. **Minute 0-2:** Triage & scope (what's broken, who's impacted)
2. **Minute 2-5:** Quick health check (pods, events, ingress)
3. **Minute 5-8:** Collect diagnostics bundle (canonical script + snapshots)
4. **Minute 8-10:** Identify likely root cause (symptoms → checks)

**Key insight:** This checklist is not about fixing the issue—it's about collecting evidence and making informed decisions.

---

## Section 4: Standard Diagnostics Collection

### The Canonical Script

LangChain provides an official diagnostics script that captures everything Support needs:

**Location:**
```
https://github.com/langchain-ai/helm/blob/main/charts/langsmith/scripts/get_k8s_debugging_info.sh
```

**What it captures:**
- Pod logs (all containers)
- Events (sorted by timestamp)
- Resource usage (CPU, memory)
- Configuration (deployments, services, ingress)
- Storage (PVCs, storage classes)
- Network (services, endpoints)

**How to use it:**
```bash
curl -O https://raw.githubusercontent.com/langchain-ai/helm/main/charts/langsmith/scripts/get_k8s_debugging_info.sh
chmod +x get_k8s_debugging_info.sh
./get_k8s_debugging_info.sh <namespace>
```

**Important:** Always run this script before making changes. The bundle it creates is your evidence.

### What Good Debugging Looks Like

**Good debugging:**
- Starts with a baseline (what was working before)
- Collects evidence systematically (checklist-driven)
- Documents hypotheses and tests them
- Preserves evidence (saves diagnostics bundles)
- Escalates with context (diagnostics + timeline)

**Bad debugging:**
- Changes things without understanding
- Doesn't collect evidence
- Jumps to conclusions
- Destroys evidence (redeploys, deletes)
- Escalates without context ("it's broken, fix it")

**The difference:** Good debugging produces a clear root cause and fix. Bad debugging produces more incidents.

---

## Section 5: Working with Support

### What Speeds Up Support

**Good escalation includes:**
- Diagnostics bundle (canonical script output)
- Timeline (when did it start, what changed)
- Symptoms (what's broken, who's impacted)
- What you've tried (investigation steps, results)
- Environment details (versions, configuration)

**Use the [Support Escalation Template](../shared/support_escalation_template.md).**

### What Slows Down Support

**Poor escalation includes:**
- No diagnostics bundle ("just look at it")
- Vague symptoms ("it's slow")
- No timeline ("it broke")
- No environment details ("it's on Kubernetes")
- Secrets in logs (security risk)

**Result:** Support has to ask for information you could have provided, delaying resolution.

### Required Metadata

**Support will always ask for:**
1. Diagnostics bundle (canonical script)
2. Helm chart version
3. Image tags (if known)
4. Recent changes (deployments, config, infrastructure)
5. Cloud provider and region
6. Kubernetes version
7. What you've tried and results

**Provide this upfront to speed resolution.**

---

## Section 6: Preventing Repeat Incidents

### Post-Incident Review

**After an incident is resolved:**
1. **Document the root cause** (what actually broke)
2. **Identify contributing factors** (what made it worse)
3. **List what worked** (what helped you debug)
4. **List what didn't work** (what slowed you down)
5. **Create action items** (what to change to prevent recurrence)

**Key questions:**
- Could we have detected this earlier? (monitoring, alerts)
- Could we have prevented this? (configuration, testing)
- Could we have fixed it faster? (runbooks, tooling)
- What did we learn? (new failure mode, new tool)

### Common Patterns

**Configuration drift:**
- Secrets rotate, but LangSmith config isn't updated
- Infrastructure changes, but Helm values aren't updated
- IdP settings change, but OIDC/SAML config isn't updated

**Prevention:** Automated validation (Module 2, Module 3 notebooks), configuration as code, regular audits.

**Resource exhaustion:**
- ClickHouse runs out of disk
- PostgreSQL hits connection limits
- Workers hit CPU/memory limits

**Prevention:** Monitoring (Module 3), autoscaling (Module 3), capacity planning.

**Network issues:**
- Egress blocked by NetworkPolicy
- Load balancer misconfiguration
- DNS resolution failures

**Prevention:** Network policy testing, ingress validation (Module 1), DNS checks.

---

## Section 7: Hands-on Failure Labs

**This is where you practice.** Each lab follows the same pattern:

1. **Baseline snapshot:** Capture what "good" looks like
2. **Introduce failure:** Apply a subtle but noticeable fault
3. **Observe symptoms:** See how the failure manifests
4. **Collect diagnostics:** Run the canonical script and gather evidence
5. **Hypothesize root cause:** Based on symptoms, identify likely cause
6. **Verify with targeted checks:** Confirm your hypothesis
7. **Remediate:** Revert the failure
8. **Confirm recovery:** Verify everything is working again
9. **Capture lessons learned:** Document what you discovered

### Lab Structure

**Each failure lab includes:**
- **What this service does for LangSmith:** Context on the service's role
- **Expected symptoms when it fails:** What you'll see when it breaks
- **Failure injection options:** Two levels (subtle vs. obvious)
- **Do the drill:** Step-by-step debugging process
- **What Support will ask for:** Service-specific evidence

### Available Labs

1. **PostgreSQL Failure Lab** (`10_failure_lab_postgres.ipynb`)
   - Connection failures, wrong credentials, network isolation
   - Symptoms: API 5xx, login failures, connection exhaustion

2. **Redis Failure Lab** (`20_failure_lab_redis.ipynb`)
   - Connectivity issues, wrong credentials
   - Symptoms: Intermittent ingestion, latency spikes, worker backlog

3. **ClickHouse Failure Lab** (`30_failure_lab_clickhouse.ipynb`)
   - Endpoint misconfiguration, network isolation, resource limits
   - Symptoms: Traces delayed/missing, insert errors, UI loads but traces don't appear

4. **Blob Storage Failure Lab** (`40_failure_lab_blob_storage.ipynb`)
   - Credential misconfiguration, bucket name errors
   - Symptoms: Large payload traces degrade ClickHouse, warnings in logs

5. **Full Incident Drill** (`90_full_incident_drill.ipynb`) (optional)
   - Combined failure + timeline pressure
   - Practice "first 10 minutes" checklist
   - Produce incident summary using escalation template

---

## Section 8: Workshop Wrap-up

### What You've Learned

- How to respond to incidents systematically
- How to collect canonical diagnostics bundles
- How to debug common failure modes
- How to escalate effectively to Support
- How to prevent repeat incidents

### Next Steps

**Immediate:**
- Run through failure labs to build muscle memory
- Customize the "first 10 minutes" checklist for your environment
- Set up monitoring and alerts (Module 3)

**Ongoing:**
- Practice incident response regularly (drills)
- Keep diagnostics script updated
- Document your own failure modes and fixes
- Share learnings with your team

### Resources

- [First 10 Minutes Checklist](../shared/incident_first_10_minutes.md)
- [Support Escalation Template](../shared/support_escalation_template.md)
- [Canonical Diagnostics Script](https://github.com/langchain-ai/helm/blob/main/charts/langsmith/scripts/get_k8s_debugging_info.sh)
- Module 1: Deployment & Baseline Validation
- Module 2: Identity & Authentication
- Module 3: Production Operations & Scaling

---

## Artifacts

**Participants leave with:**
- A working incident response process
- Experience debugging real failure modes
- A diagnostics bundle collection workflow
- An escalation template customized for their environment
- Confidence to handle incidents independently

---

## Common Pitfalls

**Don't:**
- Skip the baseline snapshot (you need "before" to compare to "after")
- Redeploy before collecting evidence (destroys diagnostics)
- Ignore error messages (they're clues)
- Escalate without diagnostics bundle (slows Support)
- Delete evidence (you'll need it for post-incident review)

**Do:**
- Follow the checklist (it's battle-tested)
- Collect diagnostics early (time is evidence)
- Document your investigation (helps you and Support)
- Test your process (run drills)
- Learn from each incident (prevent repeats)

---

## Troubleshooting

**"The diagnostics script fails":**
- Check kubectl access and namespace
- Verify script is up-to-date (check GitHub)
- Run with verbose output to see what's failing

**"I can't reproduce the failure":**
- Check that failure injection was applied correctly
- Verify symptoms match expected behavior
- Try a different failure injection method (Level 2 if Level 1 didn't work)

**"The remediation doesn't work":**
- Verify you reverted the exact change you made
- Check for cascading failures (one failure caused another)
- Collect post-remediation diagnostics to compare

**"I don't understand the symptoms":**
- Review the service's role in LangSmith (lab introduction)
- Check logs for error patterns
- Compare to baseline snapshot (what changed?)

---

**Remember:** Incident response is a skill. Practice makes perfect. The more you drill, the better you'll be when real incidents happen.

