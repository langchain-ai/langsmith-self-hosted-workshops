# Module 1: Deployment & Baseline Validation

**Goal:** Deploy LangSmith self-hosted using the official Terraform and Helm repositories, establishing a supported baseline configuration.

**Duration:** ~2 hours  
**Audience:** Platform engineers, infrastructure teams, and operators deploying LangSmith for the first time  
**Prerequisites:**
- Cloud provider account with appropriate permissions
- Local tooling installed (`aws`/`az`, `terraform`, `kubectl`, `helm`, `jq`)
- LangSmith self-hosted license key
- Basic familiarity with Kubernetes (pods, services, ingress)

---

## Motivation

Most self-hosted LangSmith failures occur **before** users ever touch the product:

- Mis-sized clusters that "work" until users arrive
- Unsupported ingress setups causing connectivity issues
- In-cluster databases used past their limits
- Missing storage primitives (blob storage, persistent volumes)
- Incorrect infrastructure configuration leading to data loss

Module 1 exists to ensure every deployment starts from a **supported baseline** using the **official Terraform and Helm repositories**. This baseline becomes the foundation for production operations (Module 3) and authentication (Module 2).

---

## Outcomes

By the end of this module, participants will:

- Deploy cloud infrastructure using the official `langchain-ai/terraform` repository
- Install LangSmith using the official `langchain-ai/helm` chart
- Validate cluster readiness, storage, and ingress
- Understand *why* specific architectural choices are required
- Establish a baseline configuration for future modules
- Be ready to layer in authentication (Module 2) and production operations (Module 3)

---

## What This Module Avoids

- **SSO / OIDC / SAML:** Covered in Module 2
- **HA tuning beyond defaults:** Covered in Module 3
- **Advanced autoscaling (KEDA):** Covered in Module 3
- **Performance benchmarking:** Out of scope
- **Custom infrastructure:** We use official Terraform modules only
- **Forked repositories:** We reference official repos directly

This keeps the baseline clean, repeatable, and supportable.

---

## Architecture Baseline (What We Support)

This workshop uses a **single, opinionated baseline**:

### Compute
- **AWS:** Amazon EKS (Elastic Kubernetes Service)
- **Azure:** Azure Kubernetes Service (AKS)
- **GCP:** Google Kubernetes Engine (GKE) - coming soon

### Ingress
- **AWS:** AWS Application Load Balancer (ALB) - cloud-native load balancer only
- **Azure:** Azure Application Gateway - cloud-native load balancer only
- **Why:** Cloud-native load balancers provide automatic scaling, health checks, and integration with cloud provider services

### Datastores
- **PostgreSQL:** Managed service (RDS for AWS, Azure Database for PostgreSQL)
- **Redis:** Managed service (ElastiCache for AWS, Azure Cache for Redis)
- **ClickHouse:** Managed service (ClickHouse Cloud) OR in-cluster with EBS CSI/Azure Disk CSI
- **Why:** Managed services reduce operational overhead and provide automated backups

### Blob Storage
- **AWS:** S3 (Simple Storage Service) - **required for production**
- **Azure:** Azure Blob Storage - **required for production**
- **Why:** Without blob storage, ClickHouse table size explodes under load, making the system unusable

### Provisioning
- **Infrastructure:** Terraform (official `langchain-ai/terraform` repository)
- **Application:** Helm (official `langchain-ai/helm` chart)

### Deviations

Deviations from this baseline are discussed in advanced modules but not used here. This ensures:
- Support can help troubleshoot standard configurations
- Updates and security patches are straightforward
- Documentation and runbooks apply directly

---

## Workshop Flow

### 1️⃣ Environment Readiness & Preflight (20–30 min)

**Notebook:** `01_preflight.ipynb`

**What we validate:**
- Tooling validation (cloud CLI, terraform, kubectl, helm, jq)
- Cloud provider credentials & region sanity check
- Cluster capacity expectations
- Storage prerequisites (CSI drivers, StorageClasses)
- Blob storage requirement (cloud object storage)

**Key emphasis:**
- Verify you're using the correct cloud account/subscription
- Ensure all required tools are available and in PATH
- Validate storage CSI drivers are installed
- Confirm blob storage is accessible

**Output:**
- Environment validated and ready
- Artifacts directory created
- Cloud provider identity confirmed

---

### 2️⃣ Terraform: Provisioning the Platform Substrate (45–60 min)

**Notebook:** `02_terraform_apply.ipynb`

**What we deploy:**
- Managed Kubernetes cluster (EKS/AKS)
- Managed PostgreSQL database (RDS/Azure Database)
- Managed Redis cache (ElastiCache/Azure Cache)
- Object storage for blob storage (S3/Azure Blob Storage)
- IAM/RBAC roles and policies
- Storage CSI driver addon

**Key principles:**
- Use the **official** Terraform repo (do not fork)
- Pin module versions for reproducibility
- Use remote state & locking
- Plan before applying
- Capture outputs needed for Helm

**Workflow:**
1. Clone and navigate to official Terraform repository
2. Identify correct module path for your cloud provider
3. Pin module versions in `versions.tf`
4. Configure Terraform variables (region, cluster name, database credentials)
5. Initialize Terraform (`terraform init`)
6. Create Terraform plan (`terraform plan`)
7. Review plan carefully
8. Apply infrastructure (`terraform apply`)
9. Capture outputs for Helm configuration

**Key emphasis:**
- Why we do *not* fork upstream
- Why remote state & locking matter
- What support will expect to see later
- How to interpret Terraform outputs

**Output:**
- Infrastructure deployed and healthy
- Terraform outputs captured
- Cluster accessible via kubectl

---

### 3️⃣ Helm: Installing LangSmith (45–60 min)

**Notebook:** `03_helm_install_langsmith.ipynb`

**What we install:**
- LangSmith application components
- External service connections (PostgreSQL, Redis, blob storage)
- Resource requests & limits
- Ingress configuration

**Key principles:**
- Use the **official** Helm chart (do not fork)
- Pin chart versions for reproducibility
- Create minimal, sane values file
- Inject required secrets properly
- Render templates before install
- Understand that "helm install succeeded" ≠ "system is healthy"

**Workflow:**
1. Clone and navigate to official Helm repository
2. Identify correct chart path
3. Pin chart version
4. Create minimal values file:
   - External service connections (database, cache, blob storage)
   - Resource requests & limits
   - Ingress configuration
   - Required secrets
5. Create Kubernetes secrets for sensitive values
6. Render templates (`helm template`) to validate
7. Install chart (`helm install`)
8. Verify installation (`helm status`)

**Key emphasis:**
- External services wiring (why managed services matter)
- Resource requests & limits (why they're required)
- Why "helm install succeeded" ≠ "system is healthy"
- Start with minimal values file and only configure what you need

**Output:**
- LangSmith application deployed
- Pods starting (may not be ready yet)
- Helm release created

---

### 4️⃣ Validation & Go/No-Go Checklist (20–30 min)

**Notebook:** `04_validate_ingress_and_ui.ipynb`

**What we validate:**
1. Pod readiness (all pods running)
2. License key validation (properly configured)
3. PVC binding (storage provisioned)
4. External services connectivity (PostgreSQL, Redis, blob storage)
5. Ingress provisioning (load balancer created)
6. Endpoint reachability (services accessible)
7. Basic UI availability (web interface works)
8. Basic functional test (optional trace submission)

**Key emphasis:**
- This checklist becomes your **baseline reference** for future troubleshooting
- Most issues are caught here, before real users onboard
- Validation ensures you're on a **supported path**

**Workflow:**
1. Verify all pods are running and ready
2. Validate license key is configured correctly
3. Check PVCs are bound (storage provisioned)
4. Test connectivity to external services
5. Verify ingress is provisioned and accessible
6. Test endpoint reachability (HTTPS)
7. Verify UI is accessible
8. Optional: Submit test trace to validate functionality

**Output:**
- Deployment validated and healthy
- Baseline reference established
- Ready for Module 2 (authentication)

---

### 5️⃣ Teardown & Cleanup (Optional, 30–45 min)

**Notebook:** `99_teardown.ipynb`

**What we clean up:**
- Helm release (LangSmith application)
- Kubernetes resources (secrets, PVCs)
- Terraform-managed infrastructure (cluster, database, cache, blob storage)

**Key emphasis:**
- Avoid ongoing cloud costs
- Practice proper resource lifecycle management
- Verify cleanup completed successfully

**Workflow:**
1. Uninstall Helm release
2. Clean up remaining Kubernetes resources
3. Destroy Terraform infrastructure
4. Verify all resources removed

**Output:**
- All resources destroyed
- No ongoing costs
- Clean slate for re-deployment

---

## Common Pitfalls Addressed in Module 1

### ClickHouse PVCs Stuck in `Pending`

**Symptom:** ClickHouse pods cannot start, PVCs remain in `Pending` state.

**Cause:** Missing EBS CSI driver (AWS) or Azure Disk CSI driver (Azure).

**Fix:** Install CSI driver addon before deploying LangSmith.

**Prevention:** Preflight checks validate CSI driver installation.

### Load Balancer Never Appears

**Symptom:** Ingress created but no load balancer provisioned.

**Cause:** Wrong ingress class or missing ingress controller.

**Fix:** Use cloud-native ingress class (AWS: `alb`, Azure: `azure/application-gateway`).

**Prevention:** Preflight checks validate ingress controller installation.

### Inline Trace Payloads Exploding ClickHouse

**Symptom:** ClickHouse table size grows rapidly, queries slow down.

**Cause:** Blob storage not configured, large payloads stored inline in ClickHouse.

**Fix:** Configure S3 (AWS) or Azure Blob Storage (Azure) before deployment.

**Prevention:** Preflight checks validate blob storage accessibility.

### Under-Sized Clusters That "Work" Until Users Arrive

**Symptom:** Deployment works initially but fails under load.

**Cause:** Cluster nodes too small, insufficient resources.

**Fix:** Use recommended node sizes (see service sizing baselines in Module 3).

**Prevention:** Preflight checks validate cluster capacity expectations.

### Terraform State Lock Issues

**Symptom:** `terraform apply` fails with state lock error.

**Cause:** Another process holds the lock, or previous operation didn't release lock.

**Fix:** Use remote state backend with locking (S3 + DynamoDB for AWS, Azure Storage for Azure).

**Prevention:** Terraform configuration uses remote state by default.

---

## Service Sizing Baselines

### Kubernetes Cluster

**Production baseline:**
- **Node instance type:** m5.xlarge (4 vCPU, 16 GB RAM) minimum
- **Node count:** 3+ nodes (for HA)
- **Storage:** EBS gp3 (AWS) or Premium SSD (Azure) with 100+ GB per node

**Non-production guidance:**
- m5.large (2 vCPU, 8 GB RAM) acceptable for development
- 2 nodes sufficient for non-production

### PostgreSQL

**Production baseline:**
- **Instance size:** db.r5.xlarge (4 vCPU, 32 GB RAM) minimum
- **Storage:** 500 GB+ with autoscaling enabled
- **High availability:** Multi-AZ deployment (RDS) or read replicas (Azure)

**Non-production guidance:**
- db.t3.medium (2 vCPU, 4 GB RAM) acceptable for development
- Single-AZ acceptable for non-production

### Redis

**Production baseline:**
- **Instance type:** cache.r6g.xlarge (6 vCPU, 13.07 GB RAM) minimum
- **High availability:** Redis Cluster mode enabled (3+ nodes)

**Non-production guidance:**
- cache.t3.micro acceptable for development
- Single node acceptable for non-production

### ClickHouse

**Production baseline:**
- **Deployment:** Managed ClickHouse (ClickHouse Cloud) OR in-cluster with EBS CSI
- **In-cluster sizing:** 3-node cluster minimum (for HA)
- **Resources per node:** 8 CPU, 32 GB RAM, 1 TB storage

**Non-production guidance:**
- Single node acceptable for development
- 4 CPU, 16 GB RAM per node sufficient

---

## Blob Storage Requirement

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
- **Versioning:** Enabled for data protection
- **Encryption:** Server-side encryption enabled

**Non-production:**
- Local MinIO or in-cluster object storage acceptable
- Access keys acceptable (not for production)
- No versioning required

---

## Terraform Best Practices

### Use Official Repository

**Why:**
- Support expects standard configurations
- Updates and security patches are provided
- Documentation and examples are maintained
- Compatibility with Helm chart is guaranteed

**How:**
- Clone `langchain-ai/terraform` repository
- Reference modules directly (do not fork)
- Pin module versions in `versions.tf`

### Remote State & Locking

**Why:**
- Prevents concurrent modifications
- Enables team collaboration
- Provides state history
- Prevents state corruption

**Configuration:**
- **AWS:** S3 backend with DynamoDB table for locking
- **Azure:** Azure Storage backend with blob container

### Plan Before Apply

**Why:**
- Review changes before applying
- Catch configuration errors early
- Understand resource impact
- Validate variable values

**Workflow:**
1. `terraform init` - Initialize backend and modules
2. `terraform plan` - Generate execution plan
3. Review plan carefully
4. `terraform apply` - Apply changes

---

## Helm Best Practices

### Use Official Chart

**Why:**
- Support expects standard configurations
- Updates and security patches are provided
- Documentation and examples are maintained
- Compatibility with Terraform outputs is guaranteed

**How:**
- Clone `langchain-ai/helm` repository
- Reference chart directly (do not fork)
- Pin chart version

### Minimal Values File

**Principle:** Start with minimal configuration and only add what you need.

**Why:**
- Reduces complexity
- Fewer points of failure
- Easier to troubleshoot
- Clearer configuration intent

**What to include:**
- External service connections (database, cache, blob storage)
- Resource requests & limits
- Ingress configuration
- Required secrets

**What to avoid:**
- Configuration for services you're not using
- Over-optimization before baseline works
- Custom modifications without justification

### Render Before Install

**Why:**
- Validate template syntax
- Review generated manifests
- Catch configuration errors early
- Understand what will be deployed

**Command:**
```bash
helm template <release-name> <chart-path> -f <values-file> -n <namespace>
```

---

## Validation Checklist

See `notebooks/module-1/04_validate_ingress_and_ui.ipynb` for complete validation.

**Quick checklist:**
- [ ] All pods running and ready
- [ ] License key configured correctly
- [ ] PVCs bound (storage provisioned)
- [ ] External services accessible (PostgreSQL, Redis, blob storage)
- [ ] Ingress provisioned and accessible
- [ ] Endpoint reachable via HTTPS
- [ ] UI accessible in browser
- [ ] Basic functional test passes (optional)

---

## Artifacts Participants Leave With

1. **Working baseline deployment**
   - LangSmith accessible via HTTPS
   - All services healthy and connected
   - Ingress configured correctly

2. **Pinned Terraform + Helm configuration**
   - Terraform module versions documented
   - Helm chart version documented
   - Values file saved and version controlled

3. **Validated ingress endpoint**
   - HTTPS URL accessible
   - TLS certificate valid
   - DNS configured correctly

4. **Readiness checklist**
   - Validation results documented
   - Baseline reference established
   - Troubleshooting evidence collected

5. **Confidence they're on a supported path**
   - Official repositories used
   - Standard configuration applied
   - Support can help troubleshoot

---

## Next Steps

1. **Run the validation notebook:**
   - `notebooks/module-1/04_validate_ingress_and_ui.ipynb`
   - Address any failures before proceeding

2. **Proceed to Module 2:**
   - Configure authentication (OIDC/SAML)
   - Set up role mapping
   - Validate SSO flows

3. **Proceed to Module 3:**
   - Configure production operations
   - Set up autoscaling
   - Establish observability

---

## References

- [Official Terraform Repository](https://github.com/langchain-ai/terraform)
- [Official Helm Repository](https://github.com/langchain-ai/helm)
- LangSmith Self-Hosted Documentation
- Cloud Provider Documentation (AWS EKS, Azure AKS)

---

## Troubleshooting

### Common Issues

**Terraform apply fails:**
- Check cloud provider credentials
- Verify IAM permissions
- Review Terraform plan for errors
- Check remote state backend configuration

**Helm install fails:**
- Verify chart path is correct
- Check values file syntax
- Validate secrets exist
- Review Helm template output

**Pods not starting:**
- Check pod logs: `kubectl logs <pod> -n <namespace>`
- Check events: `kubectl get events -n <namespace>`
- Verify resource requests/limits
- Check PVC binding status

**Ingress not accessible:**
- Verify ingress controller installed
- Check ingress class matches controller
- Verify DNS configuration
- Check TLS certificate validity

**External services not accessible:**
- Verify network connectivity (VPC/VNet)
- Check security group/NSG rules
- Validate connection strings
- Test connectivity from pod

For detailed troubleshooting, see the validation notebook and Module 3 operations guide.

