# Operations Signals and Thresholds

**Purpose:** Define early warning signals and red flag thresholds for LangSmith operations  
**Use:** Configure monitoring and alerting based on these thresholds  
**Frequency:** Review quarterly and adjust based on historical data

---

## Signal Categories

### Critical Signals (Red Flags - Immediate Action)

**Pod Health:**
- Pod in `CrashLoopBackOff` state → **IMMEDIATE**
- Pod `Pending` for > 10 minutes → **IMMEDIATE**
- Pod restart count > 5 in 1 hour → **IMMEDIATE**
- Pod `ImagePullBackOff` → **IMMEDIATE**

**Resource Saturation:**
- Node CPU > 90% for > 5 minutes → **IMMEDIATE**
- Node memory > 95% for > 5 minutes → **IMMEDIATE**
- Pod CPU > 90% for > 10 minutes → **IMMEDIATE**
- Pod memory > 95% for > 10 minutes → **IMMEDIATE**

**Application Health:**
- API server error rate > 5% → **IMMEDIATE**
- API server latency p95 > 5 seconds → **IMMEDIATE**
- Worker queue depth > 200 → **IMMEDIATE**
- Worker processing rate < 10 jobs/minute → **IMMEDIATE**

**Data Store Health:**
- PostgreSQL connection pool exhausted → **IMMEDIATE**
- PostgreSQL query timeout > 10 seconds → **IMMEDIATE**
- Redis out of memory → **IMMEDIATE**
- Redis connection refused → **IMMEDIATE**
- ClickHouse query timeout > 10 seconds → **IMMEDIATE**
- ClickHouse table size > 1 TB (single table) → **IMMEDIATE**

### Warning Signals (Yellow Flags - Monitor Closely)

**Pod Health:**
- Pod restart count > 2 in 1 hour → **WARNING**
- Pod `Pending` for > 5 minutes → **WARNING**
- Pod CPU > 70% for > 10 minutes → **WARNING**
- Pod memory > 80% for > 10 minutes → **WARNING**

**Application Health:**
- API server error rate > 1% → **WARNING**
- API server latency p95 > 2 seconds → **WARNING**
- Worker queue depth > 50 → **WARNING**
- Worker processing rate < 50 jobs/minute → **WARNING**

**Data Store Health:**
- PostgreSQL connections > 80% of max → **WARNING**
- PostgreSQL query latency p95 > 2 seconds → **WARNING**
- Redis memory > 90% → **WARNING**
- Redis hit rate < 80% → **WARNING**
- ClickHouse query latency p95 > 3 seconds → **WARNING**
- ClickHouse disk usage > 80% → **WARNING**

---

## Threshold Definitions

### Pod Restart Count

**Measurement:** `kubectl get pods -n <namespace> --field-selector=status.phase=Running` → count restarts

**Calculation:**
```bash
kubectl get pods -n <namespace> -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.status.containerStatuses[0].restartCount}{"\n"}{end}'
```

**Thresholds:**
- **Critical:** > 5 restarts in 1 hour
- **Warning:** > 2 restarts in 1 hour

**Action:**
- Check pod logs: `kubectl logs <pod> -n <namespace> --tail=100`
- Check events: `kubectl get events -n <namespace> --sort-by=.lastTimestamp`
- Check resource limits: `kubectl describe pod <pod> -n <namespace>`

### Pending Pods

**Measurement:** Pods in `Pending` state

**Calculation:**
```bash
kubectl get pods -n <namespace> --field-selector=status.phase=Pending
```

**Thresholds:**
- **Critical:** Pending for > 10 minutes
- **Warning:** Pending for > 5 minutes

**Action:**
- Check events: `kubectl describe pod <pod> -n <namespace>`
- Check node capacity: `kubectl top nodes`
- Check PVC binding: `kubectl get pvc -n <namespace>`

### API Server Error Rate

**Measurement:** HTTP 5xx responses / total requests

**Calculation:**
- Application metrics: `rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m])`
- Or: Check application logs for error patterns

**Thresholds:**
- **Critical:** > 5% error rate
- **Warning:** > 1% error rate

**Action:**
- Check pod logs: `kubectl logs <api-pod> -n <namespace> --tail=100 | grep -i error`
- Check downstream services (PostgreSQL, Redis, ClickHouse)
- Check resource usage: `kubectl top pod <api-pod> -n <namespace>`

### Worker Queue Depth

**Measurement:** Number of jobs in Redis queue

**Calculation:**
```bash
# Redis CLI
redis-cli LLEN langsmith:jobs:traces
```

**Or via application metrics:**
- KEDA metrics: `redis_queue_length`

**Thresholds:**
- **Critical:** > 200 jobs
- **Warning:** > 50 jobs

**Action:**
- Scale workers: Check KEDA ScaledObject
- Check worker processing rate
- Check for stuck jobs

### PostgreSQL Connection Count

**Measurement:** Active connections / max connections

**Calculation:**
```sql
SELECT count(*) FROM pg_stat_activity;
SELECT setting FROM pg_settings WHERE name = 'max_connections';
```

**Or via cloud provider metrics:**
- AWS RDS: `DatabaseConnections` metric
- Azure Database: `active_connections` metric

**Thresholds:**
- **Critical:** > 90% of max connections
- **Warning:** > 80% of max connections

**Action:**
- Check for connection leaks
- Review connection pool configuration
- Consider increasing max connections (if justified)

### Redis Memory Usage

**Measurement:** Used memory / max memory

**Calculation:**
```bash
redis-cli INFO memory
# used_memory / maxmemory
```

**Or via cloud provider metrics:**
- AWS ElastiCache: `DatabaseMemoryUsagePercentage`
- Azure Cache: `usedmemorypercentage`

**Thresholds:**
- **Critical:** > 95% memory usage
- **Warning:** > 90% memory usage

**Action:**
- Check for memory leaks
- Review key expiration policies
- Consider scaling up instance size

### ClickHouse Query Latency

**Measurement:** p95 query latency

**Calculation:**
- ClickHouse system tables: `SELECT quantile(0.95)(query_duration_ms) FROM system.query_log WHERE event_time > now() - INTERVAL 1 HOUR`

**Thresholds:**
- **Critical:** p95 > 10 seconds
- **Warning:** p95 > 3 seconds

**Action:**
- Check table sizes (may need partitioning)
- Check for slow queries: `SELECT * FROM system.query_log WHERE query_duration_ms > 5000 ORDER BY query_duration_ms DESC LIMIT 10`
- Check disk I/O: `kubectl top pod <clickhouse-pod> -n <namespace>`

---

## Log Patterns to Monitor

### Common Failure Patterns

**Connection Refused:**
```bash
kubectl logs <pod> -n <namespace> --tail=100 | grep -i "connection refused"
```

**Timeouts:**
```bash
kubectl logs <pod> -n <namespace> --tail=100 | grep -i "timeout"
```

**Out of Memory:**
```bash
kubectl logs <pod> -n <namespace> --tail=100 | grep -i "out of memory\|OOM"
```

**Database Errors:**
```bash
kubectl logs <pod> -n <namespace> --tail=100 | grep -i "database\|postgres\|redis\|clickhouse" | grep -i "error\|fail"
```

**Authentication Errors:**
```bash
kubectl logs <pod> -n <namespace> --tail=100 | grep -i "unauthorized\|forbidden\|auth"
```

---

## Escalation Evidence

When escalating to support, gather:

1. **Pod Status:**
   ```bash
   kubectl get pods -n <namespace> -o wide
   kubectl describe pod <problem-pod> -n <namespace>
   ```

2. **Recent Events:**
   ```bash
   kubectl get events -n <namespace> --sort-by=.lastTimestamp | tail -50
   ```

3. **Resource Usage:**
   ```bash
   kubectl top pods -n <namespace>
   kubectl top nodes
   ```

4. **Pod Logs:**
   ```bash
   kubectl logs <pod> -n <namespace> --tail=200
   ```

5. **Application Metrics:**
   - Error rates, latencies, queue depths
   - Database connection counts
   - Cache hit rates

6. **Configuration:**
   - Helm values (redacted)
   - Environment variables (redacted)
   - Resource requests/limits

---

## Threshold Tuning

**Initial thresholds:** Use the values above as starting points.

**Tuning process:**
1. Monitor for 1-2 weeks
2. Identify false positives (alerts that don't require action)
3. Identify missed incidents (issues that should have alerted)
4. Adjust thresholds based on historical data
5. Document threshold changes and rationale

**Factors to consider:**
- Workload patterns (peak hours, batch jobs)
- Growth trajectory (user growth, data growth)
- Resource capacity (cluster size, database size)
- Business requirements (SLA, RTO, RPO)

---

## Quick Reference

| Signal | Critical | Warning | Measurement |
|--------|----------|---------|-------------|
| Pod restarts | > 5/hour | > 2/hour | `kubectl get pods` |
| Pending pods | > 10 min | > 5 min | `kubectl get pods` |
| API error rate | > 5% | > 1% | Application metrics |
| Worker queue | > 200 | > 50 | Redis queue length |
| PostgreSQL connections | > 90% max | > 80% max | Database metrics |
| Redis memory | > 95% | > 90% | Redis INFO memory |
| ClickHouse latency | > 10s p95 | > 3s p95 | Query log |

---

## Next Steps

1. **Configure alerts** based on these thresholds
2. **Test alerts** to ensure they fire correctly
3. **Document runbooks** for each alert type
4. **Review quarterly** and adjust based on experience

