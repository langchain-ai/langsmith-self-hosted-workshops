# Sidecars & Service Mesh (Istio)

**Purpose:** Guide for enabling and operating Istio sidecars in LangSmith deployments  
**Audience:** Platform engineers and operators managing service mesh configurations  
**Prerequisites:** Istio installed in cluster (out of scope for this guide)

---

## When Sidecars Are Needed

### Use Cases

**Egress Control:**
- Restrict outbound traffic to approved destinations only
- Prevent pods from accessing unauthorized external services
- Enforce network policies at the service mesh level

**mTLS (Mutual TLS):**
- Encrypt traffic between services within the cluster
- Provide service-to-service authentication
- Meet compliance requirements for encrypted communication

**Policy Enforcement:**
- Rate limiting between services
- Circuit breakers for fault tolerance
- Traffic splitting for canary deployments

**Observability:**
- Distributed tracing across services
- Service-level metrics collection
- Request/response logging

### When NOT Needed

**Simple deployments:**
- Development environments
- Proof-of-concept deployments
- Single-service deployments

**No egress requirements:**
- All traffic stays within cluster
- No external database connections
- No outbound API calls

**Alternative solutions:**
- Network policies (Kubernetes native)
- Ingress controllers (for north-south traffic)
- Application-level rate limiting

---

## How to Enable Injection Safely

### Namespace-Level Injection (Recommended)

**Best for:** LangSmith namespace (all workloads need sidecars)

**Configuration:**
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: langsmith
  labels:
    istio-injection: enabled
    istio-discovery: enabled
```

**Apply:**
```bash
kubectl label namespace langsmith istio-injection=enabled istio-discovery=enabled
```

**Verification:**
```bash
kubectl get namespace langsmith --show-labels
```

**Behavior:**
- All new pods in namespace get sidecars automatically
- Existing pods require restart to get sidecars
- Pods can opt out with annotation: `sidecar.istio.io/inject: "false"`

### Per-Workload Annotation (Selective Injection)

**Best for:** Specific workloads that need sidecars

**Configuration:**
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
    spec:
      containers:
      - name: api
        # ... container spec
```

**Apply:**
```bash
kubectl patch deployment langsmith-api -n langsmith -p '{"spec":{"template":{"metadata":{"annotations":{"sidecar.istio.io/inject":"true"}}}}}'
```

**Behavior:**
- Only annotated workloads get sidecars
- Works even if namespace injection is disabled
- More granular control

### Revision-Based Injection (Canary/Blue-Green)

**Best for:** Gradual rollout or canary deployments

**Configuration:**
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: langsmith
  labels:
    istio-injection: enabled
    istio.io/rev: default  # or specific revision
```

**Behavior:**
- Allows multiple Istio control planes
- Enables gradual migration
- Supports canary deployments

---

## Operational Implications

### Logging and kubectl logs Behavior

**Multi-container pods:** After sidecar injection, pods have multiple containers:
- Application container (e.g., `langsmith-api`)
- Sidecar container (`istio-proxy`)

**Default behavior:**
```bash
# This shows logs from the FIRST container (usually application)
kubectl logs <pod> -n <namespace>

# This may show proxy logs if proxy is first container
kubectl logs <pod> -n <namespace> -c istio-proxy

# Show logs from specific container
kubectl logs <pod> -n <namespace> -c <container-name>

# Show logs from all containers
kubectl logs <pod> -n <namespace> --all-containers=true
```

**Common issue:** "If logs appear missing after injection, you're likely looking at the wrong container."

**Solution:**
```bash
# List containers in pod
kubectl get pod <pod> -n <namespace> -o jsonpath='{.spec.containers[*].name}'

# Get logs from application container
kubectl logs <pod> -n <namespace> -c langsmith-api

# Get logs from proxy container
kubectl logs <pod> -n <namespace> -c istio-proxy
```

### Health Probes and Timeouts

**Sidecar adds latency:**
- Sidecar intercepts health check requests
- Adds ~10-50ms latency per request
- May cause probe timeouts if thresholds are too low

**Adjust probe timeouts:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: langsmith-api
spec:
  template:
    spec:
      containers:
      - name: api
        readinessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 10
          timeoutSeconds: 5  # Increase if sidecars enabled
          failureThreshold: 3
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 30
          timeoutSeconds: 5  # Increase if sidecars enabled
          failureThreshold: 3
```

**Verification:**
```bash
# Check probe success rate
kubectl get pods -n <namespace> -o wide
# Look for pods in Ready state

# Check probe failures
kubectl describe pod <pod> -n <namespace> | grep -A 5 "Liveness\|Readiness"
```

### Egress to External Databases

**Problem:** Sidecars block outbound traffic by default.

**Solution:** Configure `ServiceEntry` for external endpoints.

**Example ServiceEntry for PostgreSQL:**
```yaml
apiVersion: networking.istio.io/v1beta1
kind: ServiceEntry
metadata:
  name: postgres-external
  namespace: langsmith
spec:
  hosts:
  - <postgres-hostname>.rds.amazonaws.com
  ports:
  - number: 5432
    name: postgres
    protocol: TCP
  location: MESH_EXTERNAL
  resolution: DNS
```

**Example ServiceEntry for Redis:**
```yaml
apiVersion: networking.istio.io/v1beta1
kind: ServiceEntry
metadata:
  name: redis-external
  namespace: langsmith
spec:
  hosts:
  - <redis-endpoint>.cache.amazonaws.com
  ports:
  - number: 6379
    name: redis
    protocol: TCP
  location: MESH_EXTERNAL
  resolution: DNS
```

**Apply:**
```bash
kubectl apply -f serviceentry-postgres.yaml -n langsmith
kubectl apply -f serviceentry-redis.yaml -n langsmith
```

**Verification:**
```bash
# Check ServiceEntry
kubectl get serviceentry -n langsmith

# Test connectivity from pod
kubectl exec -it <pod> -n langsmith -c <app-container> -- nc -zv <db-host> <port>
```

### DestinationRule for Traffic Policies

**Example DestinationRule:**
```yaml
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: postgres-dr
  namespace: langsmith
spec:
  host: <postgres-hostname>.rds.amazonaws.com
  trafficPolicy:
    connectionPool:
      tcp:
        maxConnections: 100
      http:
        http1MaxPendingRequests: 10
        http2MaxRequests: 100
    tls:
      mode: SIMPLE
```

---

## Sample Labels and Annotations

### Namespace Labels

```yaml
labels:
  istio-injection: enabled
  istio-discovery: enabled
```

### Pod Annotations

```yaml
annotations:
  sidecar.istio.io/inject: "true"  # Enable injection
  # or
  sidecar.istio.io/inject: "false" # Disable injection
```

### Complete Example

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: langsmith-api
  namespace: langsmith
spec:
  replicas: 2
  template:
    metadata:
      annotations:
        sidecar.istio.io/inject: "true"
    spec:
      containers:
      - name: api
        image: langsmith/api:latest
        ports:
        - containerPort: 8080
        readinessProbe:
          httpGet:
            path: /health
            port: 8080
          timeoutSeconds: 5
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          timeoutSeconds: 5
```

---

## Verification Commands

### Check Sidecar Injection

```bash
# List pods and containers
kubectl get pods -n langsmith -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.spec.containers[*].name}{"\n"}{end}'

# Check for istio-proxy container
kubectl get pod <pod> -n langsmith -o jsonpath='{.spec.containers[*].name}' | grep istio-proxy

# Describe pod to see all containers
kubectl describe pod <pod> -n langsmith | grep -A 10 "Containers:"
```

### Check ServiceEntry

```bash
# List ServiceEntries
kubectl get serviceentry -n langsmith

# Describe ServiceEntry
kubectl describe serviceentry <name> -n langsmith
```

### Check DestinationRule

```bash
# List DestinationRules
kubectl get destinationrule -n langsmith

# Describe DestinationRule
kubectl describe destinationrule <name> -n langsmith
```

### Test Connectivity

```bash
# Test from application container
kubectl exec -it <pod> -n langsmith -c <app-container> -- curl -v <external-url>

# Test from proxy container (if needed)
kubectl exec -it <pod> -n langsmith -c istio-proxy -- curl -v <external-url>
```

---

## Troubleshooting

### Logs Appear Missing

**Symptom:** `kubectl logs <pod>` shows no output or wrong logs.

**Cause:** Looking at wrong container (proxy instead of app).

**Solution:**
```bash
# List containers
kubectl get pod <pod> -n langsmith -o jsonpath='{.spec.containers[*].name}'

# Get logs from correct container
kubectl logs <pod> -n langsmith -c <app-container-name>
```

### Health Probes Failing

**Symptom:** Pods not becoming Ready after sidecar injection.

**Cause:** Probe timeouts too low for sidecar latency.

**Solution:** Increase `timeoutSeconds` in probe configuration.

### External Database Connection Refused

**Symptom:** Cannot connect to external PostgreSQL/Redis.

**Cause:** ServiceEntry not configured or incorrect.

**Solution:**
1. Check ServiceEntry exists: `kubectl get serviceentry -n langsmith`
2. Verify hostname matches: `kubectl describe serviceentry <name> -n langsmith`
3. Check egress policies: `kubectl get authorizationpolicy -n langsmith`

### High Latency After Injection

**Symptom:** Request latency increased after sidecar injection.

**Cause:** Normal sidecar overhead (10-50ms per request).

**Solution:** This is expected. If latency is excessive (>100ms), check:
- Proxy resource limits
- Network policies
- mTLS overhead

---

## Best Practices

1. **Start with namespace-level injection** for simplicity
2. **Adjust health probe timeouts** after injection
3. **Configure ServiceEntry** for all external dependencies
4. **Monitor proxy resource usage** (CPU/memory)
5. **Document container names** for log access
6. **Test connectivity** after configuration changes
7. **Use per-workload annotation** for selective injection

---

## References

- [Istio Documentation](https://istio.io/latest/docs/)
- [Istio Sidecar Injection](https://istio.io/latest/docs/setup/additional-setup/sidecar-injection/)
- [Istio ServiceEntry](https://istio.io/latest/docs/reference/config/networking/service-entry/)
- [Istio DestinationRule](https://istio.io/latest/docs/reference/config/networking/destination-rule/)

