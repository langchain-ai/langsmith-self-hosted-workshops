# Authentication Troubleshooting Playbook

**Purpose:** Triage tree for common authentication failures  
**Audience:** Operators troubleshooting SSO issues

---

## Triage Tree

### 1. Login Loop

**Symptoms:**
- User redirected to IdP
- User authenticates successfully
- Redirected back to LangSmith
- Immediately redirected to IdP again (infinite loop)

**Likely Causes:**
1. Redirect URI mismatch (most common)
2. Session cookie not being set (TLS/cookie issues)
3. Token validation failure
4. State parameter mismatch

**Evidence Gathering:**
```bash
# Check pod logs for redirect errors
kubectl logs <api-pod> -n <namespace> --tail=100 | grep -i "redirect\|callback\|auth"

# Check ingress configuration
kubectl get ingress -n <namespace> -o yaml

# Test redirect URI exactness
curl -I https://<domain>/auth/callback

# Check browser console for cookie errors
# (Manual check in browser developer tools)
```

**Commands:**
```bash
# Verify redirect URI in Helm values
helm get values <release> -n <namespace> | grep -i redirect

# Check environment variables
kubectl exec <pod> -n <namespace> -- env | grep -i redirect

# Verify IdP whitelist (manual check in IdP admin console)
```

**Fix:**
1. Verify redirect URI matches **exactly** (case, trailing slashes, protocol)
2. Check IdP whitelist includes exact redirect URI
3. Verify TLS certificate is valid (browser must accept cookies)
4. Check session cookie settings (SameSite, Secure flags)

---

### 2. 403/Unauthorized After Login

**Symptoms:**
- User authenticates successfully at IdP
- Redirected back to LangSmith
- Receives 403 Forbidden or "Unauthorized" error
- Cannot access any resources

**Likely Causes:**
1. Role mapping not configured
2. User not in any mapped groups
3. Workspace not assigned to user's organization
4. Claims/attributes not being sent by IdP

**Evidence Gathering:**
```bash
# Check pod logs for authorization errors
kubectl logs <api-pod> -n <namespace> --tail=100 | grep -i "403\|unauthorized\|forbidden\|role"

# Check role mapping configuration
helm get values <release> -n <namespace> | grep -i "role\|mapping\|group"

# Check user's group membership (from IdP)
# (Manual check - verify user is in expected groups)
```

**Commands:**
```bash
# Verify role mapping in Helm values
helm get values <release> -n <namespace> | grep -A 10 "roleMapping"

# Check environment variables for claim mappings
kubectl exec <pod> -n <namespace> -- env | grep -i "claim\|attribute\|group"

# Test with different user (in mapped group)
```

**Fix:**
1. Verify user is in a group that's mapped to a role
2. Check role mapping configuration in Helm values
3. Verify IdP is sending group claims/attributes
4. Assign user to appropriate group in IdP
5. Verify workspace assignment in LangSmith

---

### 3. SAML Assertion Missing Attributes

**Symptoms:**
- User authenticates successfully
- Login completes but user has no email/name
- Role mapping doesn't work
- User cannot access resources

**Likely Causes:**
1. IdP not configured to send required attributes
2. Attribute names don't match configuration
3. Attribute mapping incorrect in LangSmith

**Evidence Gathering:**
```bash
# Check logs for missing attribute errors
kubectl logs <api-pod> -n <namespace> --tail=100 | grep -i "attribute\|missing\|email\|name"

# Check SAML attribute mapping
helm get values <release> -n <namespace> | grep -i "saml.*attribute"

# Verify SAML metadata includes attribute definitions
# (Check IdP metadata XML)
```

**Commands:**
```bash
# Verify attribute mapping configuration
kubectl exec <pod> -n <namespace> -- env | grep -i "SAML.*ATTRIBUTE"

# Check SAML metadata for attribute definitions
curl <SAML_METADATA_URL> | grep -i "Attribute"

# Test with SAML tracer (browser extension) to see actual assertion
```

**Fix:**
1. Configure IdP to send required attributes (email, name, groups)
2. Verify attribute names match LangSmith configuration exactly
3. Update attribute mapping in Helm values if names differ
4. Test with SAML tracer to verify attributes in assertion

---

### 4. Redirect Mismatch

**Symptoms:**
- Login attempt fails immediately
- Error: "redirect_uri_mismatch" or similar
- User never reaches IdP login page

**Likely Causes:**
1. Redirect URI in LangSmith doesn't match IdP whitelist
2. Trailing slash mismatch
3. Protocol mismatch (http vs https)
4. Domain mismatch

**Evidence Gathering:**
```bash
# Check configured redirect URI
helm get values <release> -n <namespace> | grep -i redirect

# Verify exact redirect URI format
kubectl exec <pod> -n <namespace> -- env | grep -i REDIRECT

# Test redirect URI endpoint
curl -I https://<domain>/auth/callback
```

**Commands:**
```bash
# Compare redirect URIs
echo "LangSmith config:"
kubectl exec <pod> -n <namespace> -- env | grep OIDC_REDIRECT_URI

echo "IdP whitelist:"
# (Manual check in IdP admin console)

# Verify exact match (including trailing slashes, case)
```

**Fix:**
1. Get exact redirect URI from LangSmith configuration
2. Verify it matches IdP whitelist **exactly** (character-by-character)
3. Update IdP whitelist if needed
4. Restart LangSmith pods after configuration change

---

### 5. TLS/Callback Issues

**Symptoms:**
- IdP callback fails with TLS errors
- Browser shows "Not Secure" warning
- Certificate errors in browser console
- Callback never completes

**Likely Causes:**
1. Self-signed certificate (browser rejects)
2. Certificate chain incomplete
3. Certificate expired
4. Certificate doesn't match domain

**Evidence Gathering:**
```bash
# Check TLS certificate
openssl s_client -connect <domain>:443 -servername <domain> < /dev/null

# Check certificate expiration
echo | openssl s_client -connect <domain>:443 -servername <domain> 2>/dev/null | \
  openssl x509 -noout -dates

# Check ingress TLS configuration
kubectl get ingress -n <namespace> -o yaml | grep -A 5 tls
```

**Commands:**
```bash
# Verify certificate validity
kubectl get ingress -n <namespace> -o jsonpath='{.items[0].spec.tls[0].secretName}'
kubectl get secret <tls-secret> -n <namespace> -o yaml

# Test certificate from pod
kubectl exec <pod> -n <namespace> -- openssl s_client -connect <domain>:443 -servername <domain>
```

**Fix:**
1. Use valid TLS certificate from trusted CA (not self-signed)
2. Ensure full certificate chain is present
3. Renew certificate if expired
4. Verify certificate matches domain exactly
5. Update ingress TLS secret if needed

---

## What Support Will Ask For

When contacting LangSmith support for authentication issues, provide:

### Minimal Evidence Bundle

1. **Configuration Summary (redacted)**
   - Auth provider type (OIDC/SAML)
   - Issuer/metadata URL (no secrets)
   - Domain
   - Claim/attribute mappings
   - Role mapping configuration

2. **Pod Logs**
   - Last 200 lines from API/server pods
   - Filtered for auth-related errors
   - Timestamp of failure

3. **Recent Events**
   ```bash
   kubectl get events -n <namespace> --sort-by=.lastTimestamp > events.txt
   ```

4. **Ingress Configuration**
   ```bash
   kubectl get ingress -n <namespace> -o yaml > ingress.yaml
   ```

5. **Helm Values (redacted)**
   ```bash
   helm get values <release> -n <namespace> > helm-values.txt
   # Manually redact secrets before sending
   ```

### Do NOT Include

- Client secrets
- Tokens
- Passwords
- Private keys
- Full certificate chains (public certs OK)

### Support Bundle Script

```bash
#!/bin/bash
# Collect minimal auth troubleshooting bundle

NAMESPACE="${NAMESPACE:-langsmith}"
RELEASE="${HELM_RELEASE:-langsmith}"
OUTPUT_DIR="auth-support-$(date +%Y%m%d-%H%M%S)"

mkdir -p "$OUTPUT_DIR"

# Pod logs (last 200 lines, auth-related)
kubectl get pods -n "$NAMESPACE" -o jsonpath='{.items[*].metadata.name}' | \
  tr ' ' '\n' | grep -E "(api|server|backend)" | head -3 | while read pod; do
    kubectl logs "$pod" -n "$NAMESPACE" --tail=200 | \
      grep -i -E "(auth|oidc|saml|sso|login|redirect)" > "$OUTPUT_DIR/${pod}-auth-logs.txt" || true
  done

# Events
kubectl get events -n "$NAMESPACE" --sort-by=.lastTimestamp > "$OUTPUT_DIR/events.txt"

# Ingress
kubectl get ingress -n "$NAMESPACE" -o yaml > "$OUTPUT_DIR/ingress.yaml"

# Helm values (redact secrets manually)
helm get values "$RELEASE" -n "$NAMESPACE" > "$OUTPUT_DIR/helm-values.txt"
echo "⚠️  REDACT SECRETS FROM helm-values.txt BEFORE SENDING"

# Configuration summary
cat > "$OUTPUT_DIR/config-summary.txt" <<EOF
Auth Configuration Summary
Generated: $(date -Iseconds)

Namespace: $NAMESPACE
Release: $RELEASE
Domain: ${LANGSMITH_DOMAIN:-N/A}
Provider: ${AUTH_PROVIDER:-N/A}

Note: Secrets not included for security.
EOF

echo "Support bundle saved to: $OUTPUT_DIR"
echo "⚠️  Review and redact secrets before sending to support"
```

---

## Quick Reference

### OIDC Issues
- **Redirect mismatch:** Check exact URI match
- **Token validation:** Check issuer URL, clock skew
- **Missing claims:** Verify scopes and IdP configuration

### SAML Issues
- **Missing attributes:** Check IdP attribute configuration
- **Signature failure:** Verify certificate in metadata
- **Entity ID mismatch:** Check entity ID configuration

### Common Commands
```bash
# Check auth configuration
kubectl exec <pod> -n <namespace> -- env | grep -i -E "(auth|oidc|saml)"

# Check logs
kubectl logs <pod> -n <namespace> --tail=100 | grep -i auth

# Check Helm values
helm get values <release> -n <namespace>

# Restart pods (after config change)
kubectl rollout restart deployment -n <namespace>
```

---

## Escalation

If issues persist after following this playbook:

1. Collect minimal evidence bundle (see above)
2. Document exact steps to reproduce
3. Note any recent configuration changes
4. Contact LangSmith support with evidence bundle

