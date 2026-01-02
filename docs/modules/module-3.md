# Module 3: Production Operations & Scaling

**Goal:** Enable operators to run LangSmith reliably under real production load, understand scaling domains, and respond effectively when things go wrong (day-2 operations).

**Duration:** ~2 hours  
**Audience:** Platform engineers, infrastructure teams, SREs, and on-call operators  
**Prerequisites:**
- Module 1 complete: LangSmith deployed and reachable (AWS/EKS or Azure/AKS baseline)
- Module 2 complete: Authentication and authorization configured (OIDC/SAML)

---

## Overview

Module 3 transitions from "it works" to "it works reliably under load." This module covers production operations, scaling strategies, observability, and the mental models needed for day-2 operations.

**What you'll accomplish:**
- Understand LangSmith's distributed architecture and scaling domains
- Configure production-grade service sizing and HA
- Implement autoscaling strategies (HPA and KEDA)
- Set up observability and early warning signals
- Validate production readiness
- Prepare for incident response

**What this module avoids:**
- Deep dives into specific monitoring tools (Prometheus/Grafana setup)
- Custom alerting rule creation (covered in incident response)
- Performance tuning and optimization (out of scope)
- Multi-region deployments (advanced topic)

---

## Section 1: Production Mental Model

### Distributed System Reality

LangSmith is a **distributed system** with multiple services that must coordinate:

- **API Server:** Handles HTTP requests, authentication, routing
- **Workers:** Process traces, spans, and evaluations asynchronously
- **ClickHouse:** Time-series data storage and queries
- **PostgreSQL:** Metadata, users, workspaces, projects
- **Redis:** Caching, rate limiting, job queues
- **Blob Storage:** Large payload storage (traces, artifacts)

**Key insight:** These services have different scaling characteristics and failure modes. Understanding these differences is critical for production operations.

### Scaling Domains

**Scaling domains** are groups of resources that scale together or have shared bottlenecks:

1. **Ingestion Domain:**
   - API server pods (stateless, horizontal scaling)
   - Ingress/Load Balancer (cloud-managed, scales automatically)
   - **Bottleneck:** API server CPU/memory under high request volume

2. **Processing Domain:**
   - Worker pods (stateless, horizontal scaling)
   - Redis (single instance or cluster, vertical scaling)
   - **Bottleneck:** Worker capacity and Redis throughput

3. **Storage Domain:**
   - ClickHouse (stateful, complex scaling)
   - PostgreSQL (stateful, vertical scaling + read replicas)
   - Blob Storage (cloud-managed, effectively unlimited)
   - **Bottleneck:** ClickHouse query performance, PostgreSQL connection limits

4. **Control Plane:**
   - Kubernetes cluster (managed service)
   - Helm releases, ConfigMaps, Secrets
   - **Bottleneck:** Cluster capacity and node resources

**Critical understanding:** Scaling one domain without addressing downstream bottlenecks creates cascading failures.

---

## Section 2: Scaling Model

### What Scales Well

**Horizontal scaling (add more pods):**
- API server pods (stateless HTTP handlers)
- Worker pods (stateless job processors)
- Ingress controllers (cloud-managed load balancers)

**Why:** These services are stateless and can be scaled independently based on load.

### What Does NOT Autoscale

**Vertical scaling only (increase resources per instance):**
- PostgreSQL (managed RDS/Azure Database)
- Redis (managed ElastiCache/Azure Cache)
- ClickHouse (in-cluster or managed, complex scaling)

**Why:** These are stateful services with data locality requirements. Scaling requires careful planning and may involve downtime.

**Manual scaling required:**
- Kubernetes node capacity (cluster autoscaling helps, but has limits)
- Blob storage buckets (unlimited capacity, but requires configuration)
- Network bandwidth (cloud-managed, but has limits)

### Failure Pattern: HPA Increases Ingestion → Downstream Saturation

**Common anti-pattern:**

1. High request volume triggers HPA to scale API server pods
2. API servers successfully handle more requests
3. Workers cannot keep up with increased trace volume
4. Redis queue fills up
5. ClickHouse ingestion rate saturates
6. PostgreSQL connection pool exhausts
7. System degrades despite "scaled" API servers

**Solution:** Scale all domains together, or implement backpressure and rate limiting.

**Key principle:** Monitor downstream services, not just upstream services.

---

## Section 3: Service Sizing Baselines

### PostgreSQL (Database)

**Production baseline:**
- **Instance size:** db.r5.xlarge (4 vCPU, 32 GB RAM) minimum
- **Storage:** 500 GB+ with autoscaling enabled
- **High availability:** Multi-AZ deployment (RDS) or read replicas (Azure)
- **Connection pool:** 100+ connections configured in LangSmith
- **Backups:** Automated daily backups with 7-day retention minimum

**Non-production guidance:**
- db.t3.medium (2 vCPU, 4 GB RAM) acceptable for development
- Single-AZ acceptable for non-production
- 30-day backup retention sufficient

**Verification:**
```bash
# AWS RDS
aws rds describe-db-instances --db-instance-identifier <instance-id>

# Azure Database
az postgres flexible-server show --name <server-name> --resource-group <rg>
```

**What to check:**
- Instance class/size
- Multi-AZ status
- Storage autoscaling enabled
- Backup retention period
- Private networking (VPC/subnet configuration)

### Redis (Cache)

**Production baseline:**
- **Instance type:** cache.r6g.xlarge (6 vCPU, 13.07 GB RAM) minimum
- **High availability:** Redis Cluster mode enabled (3+ nodes)
- **Memory:** 50% headroom for growth
- **Persistence:** AOF (Append Only File) enabled for durability

**Non-production guidance:**
- cache.t3.micro acceptable for development
- Single node acceptable for non-production
- RDB snapshots sufficient (no AOF required)

**Verification:**
```bash
# AWS ElastiCache
aws elasticache describe-cache-clusters --cache-cluster-id <cluster-id>

# Azure Cache
az redis show --name <cache-name> --resource-group <rg>
```

**What to check:**
- Node type and memory size
- Cluster mode enabled (production)
- AOF persistence enabled
- Private networking

### ClickHouse

**Production baseline:**
- **Deployment:** Managed ClickHouse (ClickHouse Cloud) OR in-cluster with EBS CSI
- **In-cluster sizing:** 3-node cluster minimum (for HA)
- **Resources per node:** 8 CPU, 32 GB RAM, 1 TB storage
- **Storage:** EBS gp3 volumes with 3000 IOPS
- **Replication:** 2x replication factor (6 total pods for 3-node cluster)

**Non-production guidance:**
- Single node acceptable for development
- 4 CPU, 16 GB RAM per node sufficient
- 100 GB storage per node

**Verification:**
```bash
# In-cluster ClickHouse
kubectl get statefulset -n <namespace> | grep clickhouse
kubectl get pvc -n <namespace> | grep clickhouse

# Check ClickHouse cluster status
kubectl exec -it <clickhouse-pod> -n <namespace> -- clickhouse-client --query "SELECT * FROM system.clusters"
```

**What to check:**
- StatefulSet replica count
- PVC size and storage class
- Resource requests/limits
- Replication factor

### Managed vs In-Cluster

**Managed services (recommended for production):**
- PostgreSQL: RDS (AWS) or Azure Database for PostgreSQL
- Redis: ElastiCache (AWS) or Azure Cache for Redis
- ClickHouse: ClickHouse Cloud (managed service)

**Benefits:**
- Automated backups and maintenance
- High availability built-in
- Security patches applied automatically
- Monitoring and alerting included

**In-cluster services (acceptable for non-production):**
- PostgreSQL: Postgres operator (Crunchy Data, Zalando)
- Redis: Redis operator or Helm chart
- ClickHouse: ClickHouse operator

**Trade-offs:**
- More operational overhead
- Requires backup strategy
- Manual HA configuration
- Lower cost for development

### Private Networking

**Production requirement:** All data stores must be in private subnets with no public internet access.

**Why:**
- Security: Reduces attack surface
- Compliance: Required for many compliance frameworks
- Performance: Lower latency within VPC/VNet

**Verification:**
- RDS/Azure Database: Check subnet group (private subnets only)
- ElastiCache/Azure Cache: Check subnet group (private subnets only)
- ClickHouse: Check pod network policies and service mesh egress rules

---

## Section 4: Blob Storage REQUIRED for Production

### Why Blob Storage is Required

**Problem without blob storage:**
- Large trace payloads stored inline in ClickHouse
- ClickHouse table size explodes
- Query performance degrades
- Storage costs increase dramatically
- System becomes unusable under load

**Solution with blob storage:**
- Large payloads stored in S3/Azure Blob Storage
- ClickHouse stores only references (small strings)
- Query performance remains stable
- Storage costs scale linearly
- System handles production load

### Requirements

**Production:**
- **Service:** S3 (AWS) or Azure Blob Storage (Azure)
- **Bucket/Container:** Dedicated bucket for LangSmith
- **Access:** IAM roles (AWS) or Managed Identity (Azure) - no access keys
- **Lifecycle policies:** Configured for cost optimization (move to Glacier/Cool tier after 90 days)
- **Versioning:** Enabled for data protection
- **Encryption:** Server-side encryption enabled

**Non-production:**
- Local MinIO or in-cluster object storage acceptable
- Access keys acceptable (not for production)
- No lifecycle policies required

### Verification

**Check Helm values:**
```yaml
blobStorage:
  provider: s3  # or azure
  bucket: langsmith-traces
  region: us-west-2
  # IAM role ARN (not access keys)
  iamRoleArn: arn:aws:iam::<account>:role/langsmith-blob-storage
```

**Check environment variables:**
```bash
kubectl exec <api-pod> -n <namespace> -- env | grep -i blob
kubectl exec <api-pod> -n <namespace> -- env | grep -i s3
```

**What to verify:**
- Blob storage provider configured (not "local" or "filesystem")
- Bucket/container name present
- IAM role or managed identity configured (no access keys)
- Blob storage health check passes (see ops sanity checks notebook)

---

## Section 5: Autoscaling Strategy

### HPA (Horizontal Pod Autoscaler) for API Servers

**Use case:** Scale API server pods based on CPU/memory utilization.

**Configuration:**
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: langsmith-api
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: langsmith-api
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

**Baseline:**
- **Min replicas:** 2 (for HA)
- **Max replicas:** 10 (adjust based on cluster capacity)
- **CPU target:** 70% average utilization
- **Memory target:** 80% average utilization

**Verification:**
```bash
kubectl get hpa -n <namespace>
kubectl describe hpa langsmith-api -n <namespace>
```

### KEDA for Bursty Worker Scaling

**Why KEDA instead of HPA:**
- Workers process jobs from Redis queues
- Queue depth is a better scaling signal than CPU/memory
- Bursty workloads need rapid scaling (seconds, not minutes)
- KEDA supports Redis queue depth metrics

**Configuration:**
```yaml
apiVersion: keda.sh/v1alpha1
kind: ScaledObject
metadata:
  name: langsmith-workers
spec:
  scaleTargetRef:
    name: langsmith-worker
  minReplicaCount: 1
  maxReplicaCount: 20
  triggers:
  - type: redis
    metadata:
      address: <redis-host>:6379
      listName: langsmith:jobs:traces
      listLength: "10"  # Scale up when queue depth > 10
```

**Baseline:**
- **Min replicas:** 1
- **Max replicas:** 20 (adjust based on workload)
- **Queue depth threshold:** 10 jobs (adjust based on processing time)
- **Cooldown period:** 30 seconds

**Verification:**
```bash
kubectl get scaledobject -n <namespace>
kubectl describe scaledobject langsmith-workers -n <namespace>
```

### What Does NOT Autoscale

**Manual scaling required:**
- PostgreSQL instance size (vertical scaling only)
- Redis cluster size (add nodes manually)
- ClickHouse nodes (StatefulSet scaling requires data rebalancing)
- Kubernetes nodes (cluster autoscaler helps, but has limits)

**Key principle:** Monitor these services and scale proactively based on capacity planning, not reactively based on alerts.

---

## Section 6: Observability & Early Warning Signals

### Three Layers of Observability

**1. Kubernetes Layer:**
- Pod status, restarts, resource usage
- Node capacity and utilization
- Events and warnings
- **Tools:** `kubectl`, `kubectl top`, cluster monitoring

**2. LangSmith Application Layer:**
- Request rates, latencies, error rates
- Trace ingestion rates
- Worker queue depths
- **Tools:** Application metrics, logs, dashboards

**3. Data Store Layer:**
- PostgreSQL connection counts, query performance
- Redis memory usage, hit rates
- ClickHouse query performance, table sizes
- **Tools:** Cloud provider monitoring, database metrics

### Early Warning Signals

See `docs/shared/ops_signals_and_thresholds.md` for complete signal catalog.

**Critical signals (red flags):**
- Pod restart count > 5 in 1 hour
- Pending pods > 0 for > 5 minutes
- API server CPU > 80% for > 10 minutes
- Worker queue depth > 100
- PostgreSQL connections > 80% of max
- Redis memory > 90%
- ClickHouse query latency > 5 seconds (p95)

**Warning signals (yellow flags):**
- Pod restart count > 2 in 1 hour
- API server CPU > 70% for > 10 minutes
- Worker queue depth > 50
- PostgreSQL connections > 60% of max
- Redis memory > 75%

### Red Flag Thresholds

**Immediate action required:**
- Any pod in `CrashLoopBackOff` state
- Any pod `Pending` for > 10 minutes
- API server error rate > 5%
- Worker queue depth > 200
- PostgreSQL connection pool exhausted
- Redis out of memory
- ClickHouse query timeout > 10 seconds

**Escalation evidence:**
- Pod logs (last 100 lines)
- Recent events (`kubectl get events --sort-by=.lastTimestamp`)
- Resource usage (`kubectl top pods`)
- Application metrics snapshot
- Database connection counts

---

## Section 7: Backups, DR, and Failure Domains

### What Backups Cover

**PostgreSQL backups (managed services):**
- Automated daily backups (RDS/Azure Database)
- Point-in-time recovery (PITR) for last 7 days
- Cross-region backup replication (if configured)
- **Covers:** Database schema, user data, workspace/project metadata

**ClickHouse backups:**
- Manual backups via `clickhouse-backup` tool
- Cloud storage snapshots (if using managed ClickHouse)
- **Covers:** Trace data, span data, evaluation results

**Blob storage:**
- Versioning enabled (S3/Azure Blob)
- Lifecycle policies for cost optimization
- Cross-region replication (if configured)
- **Covers:** Large trace payloads, artifacts, files

### What Backups Do NOT Cover

**Not backed up automatically:**
- Kubernetes secrets (stored in cluster, not in backups)
- Helm values (stored in Git, not in backups)
- In-cluster ClickHouse data (unless backup job configured)
- Redis data (ephemeral cache, not backed up)
- Application configuration (ConfigMaps, stored in cluster)

**Manual backup required:**
- Kubernetes secrets (export to encrypted storage)
- Helm values files (store in Git)
- In-cluster ClickHouse (configure backup job)
- Application logs (export to log aggregation service)

### Failure Domains

**Availability Zone (AZ) failures:**
- **Impact:** Pods in one AZ unavailable
- **Mitigation:** Multi-AZ deployment (pods spread across AZs)
- **Recovery:** Kubernetes reschedules pods to healthy AZs

**Node failures:**
- **Impact:** All pods on failed node unavailable
- **Mitigation:** Multiple nodes, pod anti-affinity rules
- **Recovery:** Kubernetes reschedules pods to healthy nodes

**Database failures:**
- **Impact:** Application cannot read/write data
- **Mitigation:** Multi-AZ RDS, automated failover
- **Recovery:** RDS promotes standby to primary (5-10 minutes)

**Region failures:**
- **Impact:** Entire deployment unavailable
- **Mitigation:** Multi-region deployment (advanced, out of scope)
- **Recovery:** Manual failover to secondary region

**Reality check:** Most failures are AZ or node-level. Region failures are rare but catastrophic. Plan accordingly.

---

## Section 8: Production Readiness Checklist

See `docs/shared/production_readiness_checklist.md` for complete checklist.

**Each checklist item maps to real incidents:**

1. **Blob storage configured** → Prevents ClickHouse table explosion
2. **PostgreSQL HA enabled** → Prevents database downtime
3. **Redis cluster mode** → Prevents cache failures
4. **ClickHouse replication** → Prevents data loss
5. **HPA configured** → Prevents API server overload
6. **KEDA configured** → Prevents worker queue saturation
7. **Monitoring enabled** → Enables early detection
8. **Backups configured** → Enables data recovery
9. **Private networking** → Meets security requirements
10. **Resource limits set** → Prevents resource exhaustion

**Validation:**
- Run `notebooks/module-3/01_ops_sanity_checks.ipynb` to validate each item
- Review cloud provider console for managed service configuration
- Check Helm values for application configuration
- Verify monitoring dashboards show expected metrics

---

## Section 9: Sidecars & Service Mesh (Istio)

### When Sidecars Are Needed

**Use cases:**
- **Egress control:** Restrict outbound traffic to approved destinations
- **mTLS:** Encrypt traffic between services
- **Policy enforcement:** Rate limiting, circuit breakers
- **Observability:** Distributed tracing, metrics collection

**When NOT needed:**
- Simple deployments without egress requirements
- Development environments
- Proof-of-concept deployments

### How to Enable Injection Safely

**Namespace-level injection (recommended for LangSmith):**
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: langsmith
  labels:
    istio-injection: enabled
    istio-discovery: enabled
```

**Per-workload annotation (for selective injection):**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: langsmith-api
spec:
  template:
    metadata:
      annotations:
        sidecar.istio.io/inject: "true"
```

**Revision-based injection (for canary/blue-green):**
```yaml
labels:
  istio-injection: enabled
  istio.io/rev: default
```

### Operational Implications

**Logging and kubectl logs:**
- Multi-container pods require container selection
- **App logs:** `kubectl logs <pod> -c <container-name> -n <namespace>`
- **Proxy logs:** `kubectl logs <pod> -c istio-proxy -n <namespace>`
- **All logs:** `kubectl logs <pod> --all-containers=true -n <namespace>`

**Common issue:** "If logs appear missing after injection, you're likely looking at the wrong container."

**Health probes and timeouts:**
- Sidecar adds latency to health checks
- Increase probe timeouts if sidecars are enabled
- Verify readiness probes account for sidecar startup

**Egress to external databases:**
- Configure `ServiceEntry` for external PostgreSQL/Redis endpoints
- Configure `DestinationRule` for traffic policies
- Verify egress rules allow database connections

See `docs/shared/sidecars_and_service_mesh.md` for detailed guidance.

---

## Section 10: Transition to Incident Response

Module 3 establishes the baseline for production operations. The next step is **incident response**:

**What you'll learn:**
- How to diagnose common failure modes
- How to gather evidence for support
- How to implement runbooks
- How to perform post-incident reviews

**Prerequisites:**
- Module 3 complete (production readiness validated)
- Monitoring and alerting configured
- On-call rotation established

---

## Artifacts Participants Leave With

1. **Production readiness checklist** (completed)
2. **Service sizing documentation** (baselines documented)
3. **Autoscaling configuration** (HPA and KEDA configured)
4. **Observability setup** (signals and thresholds documented)
5. **Backup strategy** (backups configured and tested)
6. **Ops sanity checks notebook** (validation results)

---

## Next Steps

1. **Run the ops sanity checks notebook:**
   - `notebooks/module-3/01_ops_sanity_checks.ipynb`

2. **Review production readiness checklist:**
   - `docs/shared/production_readiness_checklist.md`

3. **Document your thresholds:**
   - `docs/shared/ops_signals_and_thresholds.md`

4. **Configure monitoring and alerting** (next module)

5. **Proceed to incident response training** (next module)

---

## References

- [Kubernetes HPA Documentation](https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/)
- [KEDA Documentation](https://keda.sh/docs/)
- [Istio Service Mesh](https://istio.io/latest/docs/)
- LangSmith Helm Chart Documentation
- Cloud Provider Documentation (AWS RDS, Azure Database, etc.)

