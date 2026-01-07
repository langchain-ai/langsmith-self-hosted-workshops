# Production Readiness Checklist

**Purpose:** Validate that LangSmith deployment meets production requirements  
**Use:** Complete this checklist before declaring production-ready  
**Frequency:** Review quarterly or after significant changes

---

## Infrastructure & Networking

### Cloud Provider Configuration
- [ ] Correct cloud account/subscription (verified)
- [ ] Correct region selected (verified)
- [ ] Private networking configured (all data stores in private subnets)
- [ ] VPC/VNet peering configured (if multi-VPC deployment)
- [ ] Security groups/NSGs configured correctly
- [ ] IAM roles/Managed Identities configured (no access keys)

### Kubernetes Cluster
- [ ] Cluster version supported (check compatibility matrix)
- [ ] Node capacity sufficient (headroom for scaling)
- [ ] Cluster autoscaling enabled (if applicable)
- [ ] CSI storage drivers installed (EBS CSI for AWS, Azure Disk CSI for Azure)
- [ ] Network policies configured (if required)
- [ ] Resource quotas set (if multi-tenant)

---

## Data Stores

### PostgreSQL
- [ ] Instance size meets baseline (db.r5.xlarge minimum for production)
- [ ] Multi-AZ enabled (RDS) or read replicas configured (Azure)
- [ ] Storage autoscaling enabled
- [ ] Automated backups configured (7-day retention minimum)
- [ ] Connection pool configured (100+ connections)
- [ ] Private networking (no public access)
- [ ] Encryption at rest enabled
- [ ] Performance insights/monitoring enabled

### Redis
- [ ] Instance type meets baseline (cache.r6g.xlarge minimum for production)
- [ ] Cluster mode enabled (3+ nodes for production)
- [ ] AOF persistence enabled (production)
- [ ] Memory headroom sufficient (50% free)
- [ ] Private networking (no public access)
- [ ] Encryption at rest enabled

### ClickHouse
- [ ] Deployment type: Managed (ClickHouse Cloud) OR in-cluster with proper sizing
- [ ] In-cluster: 3-node cluster minimum (for HA)
- [ ] Resources per node: 8 CPU, 32 GB RAM, 1 TB storage (production)
- [ ] Replication factor: 2x (6 total pods for 3-node cluster)
- [ ] Storage class: EBS gp3 with 3000 IOPS (AWS) or Premium SSD (Azure)
- [ ] Backups configured (if in-cluster)
- [ ] Private networking (no public access)

### Blob Storage (REQUIRED)
- [ ] Blob storage provider configured (S3 or Azure Blob Storage)
- [ ] NOT using local filesystem or in-cluster storage
- [ ] Bucket/container created and accessible
- [ ] IAM role/Managed Identity configured (no access keys)
- [ ] Versioning enabled
- [ ] Encryption at rest enabled
- [ ] Lifecycle policies configured (cost optimization)
- [ ] Health check passes (see ops sanity checks notebook)

**Critical:** Blob storage is REQUIRED for production. Without it, ClickHouse will become unusable under load.

---

## Application Configuration

### Helm Configuration
- [ ] Helm values file reviewed and documented
- [ ] Resource requests/limits set for all containers
- [ ] Replica counts set appropriately (min 2 for HA)
- [ ] Environment variables documented
- [ ] Secrets stored in Kubernetes (not in values file)
- [ ] Values file version controlled (Git)

### High Availability
- [ ] API server replicas: 2+ (for HA)
- [ ] Worker replicas: 1+ (scaled via KEDA)
- [ ] Pod anti-affinity rules configured (spread across nodes/AZs)
- [ ] Readiness probes configured correctly
- [ ] Liveness probes configured correctly

### Autoscaling
- [ ] HPA configured for API servers (CPU/memory targets)
- [ ] HPA min replicas: 2
- [ ] HPA max replicas: 10+ (adjust based on capacity)
- [ ] KEDA ScaledObject configured for workers (queue depth)
- [ ] KEDA min replicas: 1
- [ ] KEDA max replicas: 20+ (adjust based on workload)

---

## Observability

### Monitoring
- [ ] Kubernetes metrics available (pod CPU/memory)
- [ ] Application metrics exposed (request rates, latencies)
- [ ] Database metrics available (connection counts, query performance)
- [ ] Redis metrics available (memory usage, hit rates)
- [ ] ClickHouse metrics available (query latency, table sizes)
- [ ] Log aggregation configured (CloudWatch, Azure Monitor, etc.)

### Alerting
- [ ] Critical alerts configured (pod crashes, high error rates)
- [ ] Warning alerts configured (resource saturation, queue depth)
- [ ] Alert thresholds documented (see ops_signals_and_thresholds.md)
- [ ] On-call rotation configured
- [ ] Escalation paths defined

### Dashboards
- [ ] Kubernetes dashboard (pod status, resource usage)
- [ ] Application dashboard (request rates, error rates)
- [ ] Database dashboard (connection counts, query performance)
- [ ] Queue depth dashboard (worker queue metrics)

---

## Security

### Authentication & Authorization
- [ ] SSO configured (OIDC or SAML)
- [ ] Local auth disabled (production)
- [ ] Role mapping configured correctly
- [ ] Admin access restricted (minimal admins)

### Network Security
- [ ] Ingress TLS configured (valid certificate)
- [ ] mTLS enabled (if service mesh used)
- [ ] Egress policies configured (if service mesh used)
- [ ] Network policies configured (if required)

### Secrets Management
- [ ] Secrets stored in Kubernetes (not in code)
- [ ] Secrets rotation process documented
- [ ] Access to secrets restricted (RBAC)

---

## Backup & Disaster Recovery

### Backups
- [ ] PostgreSQL backups automated (daily, 7-day retention)
- [ ] ClickHouse backups configured (if in-cluster)
- [ ] Blob storage versioning enabled
- [ ] Backup restoration tested (last 6 months)

### Disaster Recovery
- [ ] DR plan documented
- [ ] RTO/RPO defined
- [ ] Failover procedure tested
- [ ] Cross-region replication configured (if required)

---

## Operational Readiness

### Documentation
- [ ] Runbooks documented (common operations)
- [ ] Incident response procedures documented
- [ ] Escalation paths documented
- [ ] Service sizing baselines documented

### Testing
- [ ] Load testing performed (validates scaling)
- [ ] Failover testing performed (validates HA)
- [ ] Backup restoration tested
- [ ] Ops sanity checks notebook run (all checks pass)

### Team Readiness
- [ ] On-call rotation established
- [ ] Team trained on operations
- [ ] Access to cloud console (for managed services)
- [ ] Access to monitoring/alerting tools

---

## Service Mesh (If Applicable)

### Istio Configuration
- [ ] Istio installed and configured
- [ ] Sidecar injection enabled (namespace or per-workload)
- [ ] ServiceEntry configured (for external databases)
- [ ] DestinationRule configured (traffic policies)
- [ ] Egress policies configured (if required)
- [ ] mTLS enabled (if required)

### Operational Considerations
- [ ] Log selection documented (app vs proxy logs)
- [ ] Health probe timeouts adjusted (account for sidecar)
- [ ] Multi-container pod logging understood

---

## Sign-Off

**Validated by:** _________________  
**Date:** _________________  
**Next Review Date:** _________________  
**Notes:** _________________

---

## Post-Checklist Actions

1. **Run ops sanity checks notebook:**
   - `notebooks/module-3/01_ops_sanity_checks.ipynb`
   - Address any failures before production

2. **Document thresholds:**
   - Update `docs/shared/ops_signals_and_thresholds.md`
   - Configure alerts based on thresholds

3. **Schedule quarterly reviews:**
   - Review checklist quarterly
   - Update baselines as workload grows
   - Adjust thresholds based on historical data

---

## Common Gaps

**Most common production readiness gaps:**
1. Blob storage not configured (CRITICAL)
2. PostgreSQL single-AZ (no HA)
3. Redis single node (no cluster mode)
4. No autoscaling configured
5. No monitoring/alerting
6. Backups not tested
7. Resource limits not set

**Address these before declaring production-ready.**

