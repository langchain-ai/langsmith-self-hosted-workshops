# LangSmith Self-Hosted Operator Workshop

This repository contains the hands-on workshop materials for deploying, operating, and troubleshooting **LangSmith Self-Hosted** in production environments.

The workshop is designed for **platform, infrastructure, and MLOps engineers** responsible for running LangSmith in enterprise settings. It emphasizes **operational correctness**, **repeatability**, and **real-world failure modes** over conceptual training.

> **Note:** This workshop assumes deployment using *NIX-based servers, preferably Linux. If you must use Windows please raise an issue in the [Github](https://github.com/langchain-ai/langsmith-self-hosted-workshops) repo and LangChain engineers will address it. 

> **Note:** This workshop uses Jupyter notebooks for its demonstrations. You have the option of running them locally via your own [Jupyter server](https://jupyter.org/) or use Google's [Github-to-Colab tool](https://githubtocolab.com) with your existing Google Suite account. 

This repo complements (but does not replace) the high-level deployment instructions [the LangSmith documentation](https://docs.langchain.com). Where the docs explain *what* to do, this workshop focuses on *how to do it safely and repeatedly*.

---

## What This Workshop Is (and Is Not)

**This workshop is:**
- Operator-focused enablement for LangSmith Self-Hosted
- Practical, production-oriented, and opinionated
- Based on supported Terraform and Helm configurations
- Designed for live delivery (virtual or in person) or self-serve execution

**This workshop is not:**
- A LangChain or LLM fundamentals course
- Application development or prompt engineering training
- A replacement for official documentation
- A certification (though it feeds into a future certification track)

---

## Workshop Structure

The workshop is organized into **four modules**, each designed to fit into a ~1–2 hour session. Modules can be delivered individually, but are most effective when completed in order.

### Module 1 — Deployment Foundations
Deploy LangSmith Self-Hosted using the **official** Terraform and Helm repositories (no forking).  
Covers AWS prerequisites, EKS cluster provisioning, RDS/ElastiCache/S3 setup, ingress configuration, and initial validation. Establishes the **supported baseline** that all subsequent modules build upon.

### Module 2 — Identity, Auth, and Access
Configure and validate enterprise authentication (OIDC / SSO), user access, and RBAC.  
Focuses on correctness and verification, not IdP-specific theory.

### Module 3 — Scaling, Reliability, and Production Readiness
Understand sizing, autoscaling, data stores (Postgres, Redis, ClickHouse, blob storage), and common bottlenecks.  
Includes guidance on production hardening and capacity planning.

### Module 4 — Troubleshooting, Incident Response, and Support
Learn how to diagnose issues under pressure, collect the right diagnostics, and work effectively with LangChain Support.  
Centers on real incidents and repeatable debugging workflows.

---

## How to Use This Repository

### Docs
The `docs/` directory contains **instructor-ready content** for each module. These files are intended to be:
- Read before a session
- Used as a facilitation guide during delivery
- Referenced after the workshop as operational guidance

### Notebooks
The `notebooks/` directory contains **execution-focused Jupyter notebooks** for modules where hands-on workflows matter most (especially Module 1 and Module 2).

Notebooks are:
- **Safe-by-default**: Destructive actions (Terraform apply, Helm install) are commented out and require explicit uncommenting
- **Environment-variable driven**: All configuration comes from `.env` files (see Getting Started)
- **Self-contained**: Shared helper modules in `notebooks/shared/` handle bootstrap, validation, and common operations
- **Designed to be re-run**: Can be executed multiple times in different AWS accounts or environments
- **Intended as guided execution**: Step-by-step workflows, not reference documentation

**Key principle:** Notebooks use the **official** Terraform and Helm repositories directly. We do **not** fork or modify upstream repos—this ensures you're on a supported path that matches what LangChain Support expects to see.

### Scripts
The `scripts/` directory contains **canonical operational scripts**, including diagnostics collection used during troubleshooting and support escalation.

These scripts are the authoritative tools referenced in Module 4 and should not be forked or duplicated.

---

## Prerequisites

### Required Knowledge

Participants should be comfortable with:
- Kubernetes fundamentals (pods, services, ingress, PVCs)
- AWS basics (IAM, VPCs, load balancers, EKS)
- Terraform and Helm (at a working level)

No prior LangSmith experience is required.

### Required Tools

The following tools must be installed and available in your `PATH`:
- `aws` CLI (configured with appropriate credentials)
- `terraform` (>= 1.0)
- `helm` (>= 3.0)
- `kubectl` (compatible with your Kubernetes version)
- `jq` (for JSON processing)
- Python 3.9+ with `pip`
- Jupyter Notebook or JupyterLab

**Important:** Notebooks automatically install required Python packages (`python-dotenv`, `pyyaml`, `requests`) on first run, but you must have the CLI tools installed beforehand.

---

## Safety and Cost Notes

- **Infrastructure created during this workshop incurs real cloud costs** (EKS clusters, RDS, ElastiCache, etc.)
- **Teardown steps are provided** in `notebooks/module-1/99_teardown.ipynb`, but **participants are responsible for cleanup**
- **Always review** environment variables, Terraform plans, and Helm rendered templates before applying changes
- **Destructive actions are disabled by default** in notebooks—you must explicitly uncomment code to apply Terraform or install Helm releases
- **Use a non-production AWS account** for workshop exercises

---

## Relationship to Official Docs

- **docs.langchain.com** explains supported architectures and concepts
- **This repo** teaches operators how to deploy, validate, and operate those architectures safely

If there is ever a conflict, official documentation and support guidance take precedence.

---

## Status and Evolution

This workshop is actively evolving based on:
- Customer deployments
- Support ticket patterns
- Infra and product feedback

The long-term goal is to feed this material into a **formal LangSmith Self-Hosted certification track**, but this repo intentionally stays focused on enablement, not testing.

---

## Getting Started

### 1. Clone Required Repositories

**Critical:** The notebooks reference the official Terraform and Helm repositories. You must clone these locally:

```bash
# Clone the official Terraform repository
git clone https://github.com/langchain-ai/terraform.git <your-terraform-path>
# Example: git clone https://github.com/langchain-ai/terraform.git ~/src/langchain-ai/terraform

# Clone the official Helm repository
git clone https://github.com/langchain-ai/helm.git <your-helm-path>
# Example: git clone https://github.com/langchain-ai/helm.git ~/src/langchain-ai/helm
```

**Do not fork these repositories.** Reference them directly to ensure you're using supported configurations.

### 2. Configure Environment Variables

1. Review the example environment files in `env-samples/`:
   - `workshop.env.example` - Main workshop configuration
   - `aws.env.example` - AWS-specific settings
   - `oidc.env.example` - OIDC/SSO configuration (Module 2)
   - `module3.env.example` - Module 3 specific settings

2. Create your local environment file:
   ```bash
   # Option 1: Create .env (if your Jupyter environment supports it)
   cp env-samples/workshop.env.example notebooks/.env
   
   # Option 2: Create workshop.env (works in all Jupyter environments)
   cp env-samples/workshop.env.example notebooks/workshop.env
   ```

3. Edit the file and set:
   - `TERRAFORM_REPO_DIR` - Path to your cloned Terraform repository
   - `HELM_REPO_DIR` - Path to your cloned Helm repository
   - `TERRAFORM_DIR` - Path to the AWS LangSmith module (typically `$TERRAFORM_REPO_DIR/modules/aws/langsmith`)
   - `HELM_CHART_REF` - Path to the LangSmith chart (typically `$HELM_REPO_DIR/charts/langsmith`)
   - `POSTGRES_USERNAME` and `POSTGRES_PASSWORD` - Database credentials for Terraform
   - `LANGSMITH_LICENSE_KEY` - Your LangSmith self-hosted license key
   - AWS configuration (`AWS_REGION`, `CLUSTER_NAME`, etc.)

### 3. Start the Workshop

1. Read `docs/modules/module-1.md` for module overview and context
2. Open `notebooks/module-1/01_aws_preflight.ipynb` in Jupyter
3. Run the bootstrap cell (first cell) to validate your environment
4. Follow the notebook cells sequentially

**Note:** The first notebook cell will automatically:
- Load your environment variables
- Check that all required tools are installed
- Validate AWS credentials
- Create an artifacts directory for outputs

---

If you are a LangChain customer and have questions about this workshop or need help running it, reach out through your usual support channels.
