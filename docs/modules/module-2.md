# Module 2: Identity & Authentication

**Duration:** ~2 hours  
**Audience:** Operators deploying and managing LangSmith self-hosted  
**Prerequisite:** Module 1 complete (working deployment with DNS/TLS/Ingress configured)

---

## Motivation

Most production LangSmith deployments require centralized identity management. Configuring SSO **before** onboarding users prevents:

- Manual user provisioning overhead
- Security gaps from shared credentials
- Compliance violations from unmanaged access
- Operational toil from authentication failures

This module ensures your authentication setup is **correct from day one**, not retrofitted after users are already in the system.

---

## Outcomes

By the end of this module, participants will:

- Understand LangSmith's authentication and authorization model
- Configure OIDC or SAML SSO with their identity provider
- Validate authentication flows end-to-end
- Map identity provider groups to LangSmith roles
- Troubleshoot common authentication failures
- Maintain authentication configuration as code

---

## What This Module Avoids

- **IdP admin tutorials:** We assume your IdP team provides required configuration values
- **SCIM deep-dive:** User provisioning via SCIM is out of scope
- **Multi-IdP scenarios:** We focus on single IdP configuration
- **Local auth production use:** Local authentication is discouraged for production deployments

---

## Supported Identity Models

### OIDC (Preferred)
- **When to use:** Modern IdPs (Okta, Azure AD, Google Workspace, Auth0)
- **Advantages:** Standard protocol, easier debugging, better error messages
- **Requirements:** OIDC-compliant IdP with client credentials

### SAML (Fallback)
- **When to use:** Legacy IdPs or enterprise requirements
- **Advantages:** Widely supported, enterprise-standard
- **Requirements:** SAML 2.0 IdP with metadata endpoint or XML file

### Local Authentication (Discouraged)
- **When to use:** Development/testing only
- **Limitations:** No centralized management, manual user creation, security risk
- **Note:** This module does not cover local auth configuration

---

## Authentication Request Flow

```
┌─────────┐         ┌──────────────┐         ┌─────────────┐
│ Browser │         │  LangSmith   │         │  Identity   │
│         │         │   (Ingress)  │         │  Provider   │
└────┬────┘         └──────┬───────┘         └──────┬──────┘
     │                     │                         │
     │ 1. GET /login       │                         │
     ├────────────────────>│                         │
     │                     │                         │
     │ 2. Redirect to IdP  │                         │
     │    (with state)     │                         │
     │<────────────────────┤                         │
     │                     │                         │
     │ 3. GET /authorize    │                         │
     ├───────────────────────────────────────────────>│
     │                     │                         │
     │ 4. User authenticates                          │
     │    (IdP UI)                                    │
     │                     │                         │
     │ 5. Callback with code/token                   │
     │<───────────────────────────────────────────────┤
     │                     │                         │
     │ 6. POST /callback   │                         │
     ├────────────────────>│                         │
     │                     │                         │
     │ 7. Exchange code for token                     │
     │                     ├─────────────────────────>│
     │                     │<─────────────────────────┤
     │                     │                         │
     │ 8. Validate token & extract claims             │
     │                     │                         │
     │ 9. Create/update user session                  │
     │                     │                         │
     │ 10. Redirect to dashboard                      │
     │<────────────────────┤                         │
     │                     │                         │
```

**Key Points:**
- Redirect URI must match **exactly** (protocol, domain, path, trailing slashes)
- State parameter prevents CSRF attacks
- Token validation includes signature, expiration, and issuer verification
- Claims mapping determines user roles and workspace access

---

## Workshop Flow

### 1. LangSmith Authentication Model

**Authentication vs Authorization:**
- **Authentication (AuthN):** "Who are you?" - Verified by IdP
- **Authorization (AuthZ):** "What can you do?" - Determined by role mapping

**Roles:**
- **Admin:** Full system access, workspace management, user management
- **Member:** Workspace access, project creation, trace viewing
- **Viewer:** Read-only access to assigned workspaces

**Workspaces & Organizations:**
- Users belong to **organizations** (top-level container)
- Users access **workspaces** within organizations
- Role mapping determines which workspaces a user can access
- **No shared admin accounts** - each user authenticates individually

**Key Principle:** Authentication is centralized (IdP), authorization is application-level (LangSmith role mapping).

---

### 2. Choosing OIDC vs SAML

**Decision Rule:**

```
IF IdP supports OIDC AND you can configure OIDC client
  → Use OIDC (preferred)
ELSE IF IdP only supports SAML OR enterprise requires SAML
  → Use SAML (fallback)
ELSE
  → Re-evaluate IdP choice
```

**OIDC Advantages:**
- Better error messages
- Easier debugging (standard endpoints)
- Modern protocol with better security defaults
- Simpler configuration

**SAML Advantages:**
- Enterprise-standard
- Widely supported
- Mature protocol

**Recommendation:** Start with OIDC unless blocked by IdP limitations or policy.

---

### 3. Configuring OIDC

#### Required IdP Inputs

Your IdP team must provide:

1. **Issuer URL** (e.g., `https://your-org.okta.com/oauth2/default`)
   - Must be HTTPS
   - Must be reachable from LangSmith pods
   - Used for discovery and token validation

2. **Client ID**
   - OAuth2 client identifier
   - Public value (safe to log)

3. **Client Secret**
   - OAuth2 client secret
   - **Never log or print**
   - Store in Kubernetes secret

4. **Redirect URI**
   - **Exact format:** `https://your-langsmith-domain.com/auth/callback`
   - Must match **exactly** (case-sensitive, no trailing slash unless specified)
   - IdP team must whitelist this URI

5. **Required Claims**
   - `email` (required): User email address
   - `name` (optional): Display name
   - `groups` (optional): Group membership for role mapping

6. **Scopes**
   - `openid` (required)
   - `email` (required)
   - `profile` (optional)
   - `groups` (optional, if using group-based role mapping)

#### Helm/Environment Configuration

**Helm Values (recommended):**

```yaml
auth:
  provider: oidc
  oidc:
    issuer: "https://your-org.okta.com/oauth2/default"
    clientId: "your-client-id"
    clientSecret:
      secretName: langsmith-oidc-secret
      secretKey: client-secret
    redirectURI: "https://your-langsmith-domain.com/auth/callback"
    scopes:
      - openid
      - email
      - profile
      - groups
    claimMapping:
      email: email
      name: name
      groups: groups
```

**Environment Variables (alternative):**

```bash
AUTH_PROVIDER=oidc
OIDC_ISSUER=https://your-org.okta.com/oauth2/default
OIDC_CLIENT_ID=your-client-id
OIDC_CLIENT_SECRET=<from-secret>
OIDC_REDIRECT_URI=https://your-langsmith-domain.com/auth/callback
OIDC_SCOPES=openid,email,profile,groups
```

#### Redirect URI Exactness

**Critical:** The redirect URI must match **exactly** between:
- LangSmith configuration
- IdP whitelist
- Actual callback URL

**Common Mistakes:**
- Trailing slash mismatch: `/auth/callback` vs `/auth/callback/`
- Protocol mismatch: `http://` vs `https://`
- Domain mismatch: `langsmith.example.com` vs `www.langsmith.example.com`
- Port mismatch: `:443` vs no port

**Validation:** Use the validation notebook to verify exact match.

#### TLS Requirements

- IdP issuer URL must be HTTPS
- LangSmith domain must have valid TLS certificate
- Certificate must be trusted by browser (not self-signed for production)
- Certificate must match domain exactly (no wildcard issues)

#### Clock Skew

- LangSmith and IdP clocks must be synchronized
- Maximum allowed skew: typically 5 minutes
- Use NTP on Kubernetes nodes
- Validate with: `kubectl exec <pod> -- date` vs IdP server time

---

### 4. Role Mapping

**Principle:** Map IdP groups to LangSmith roles, not individual users.

#### Group-Based Mapping (Recommended)

```yaml
auth:
  roleMapping:
    groups:
      - group: "langsmith-admins"
        role: "admin"
      - group: "langsmith-members"
        role: "member"
      - group: "langsmith-viewers"
        role: "viewer"
```

**Benefits:**
- Centralized management in IdP
- Easier audit trail
- Scales to large organizations

#### User-Based Mapping (Fallback)

```yaml
auth:
  roleMapping:
    users:
      - email: "admin@example.com"
        role: "admin"
```

**Use only when:**
- Group claims unavailable
- Temporary workaround
- Small team (< 10 users)

#### Minimal Admins Principle

- **Start with 1-2 admins**
- Add admins only when necessary
- Use group-based mapping for admins
- Document admin assignments

#### Mapping Claims to Roles

**Claim Structure:**

```json
{
  "email": "user@example.com",
  "name": "John Doe",
  "groups": ["langsmith-members", "engineering"]
}
```

**Mapping Logic:**
1. Extract `groups` claim
2. Match against role mapping configuration
3. Assign highest privilege role found
4. Default to "member" if no match

**Validation:** Test with users in different groups to verify mapping.

---

### 5. SAML Configuration

#### Required Metadata

Your IdP team must provide:

1. **SAML Metadata URL** (preferred)
   - HTTPS endpoint serving XML metadata
   - Must be reachable from LangSmith pods
   - Auto-refreshes configuration

2. **SAML Metadata XML** (fallback)
   - Static XML file
   - Must be updated manually when IdP changes
   - Store in Kubernetes secret or ConfigMap

#### Expected Attributes

**Required:**
- `email` or `http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress`
- `name` or `http://schemas.xmlsoap.org/ws/2005/05/identity/claims/name`

**Optional (for role mapping):**
- `groups` or `http://schemas.microsoft.com/ws/2008/06/identity/claims/groups`
- Custom attribute names (must match exactly)

#### Common Failures

1. **Missing Attributes**
   - Symptom: User authenticates but has no email/name
   - Cause: IdP not sending required attributes
   - Fix: Configure IdP to send required attributes

2. **Attribute Name Mismatch**
   - Symptom: Claims not mapped correctly
   - Cause: LangSmith expects different attribute name
   - Fix: Update attribute mapping in Helm values

3. **Signature Validation Failure**
   - Symptom: Authentication fails with "invalid signature"
   - Cause: Certificate mismatch or expired certificate
   - Fix: Update IdP certificate in metadata

4. **Assertion Expired**
   - Symptom: Authentication times out
   - Cause: Clock skew or assertion validity window too short
   - Fix: Synchronize clocks, adjust validity window

---

### 6. Validation & Failure Drills

#### Validation Checklist

See `docs/shared/auth_validation_checklist.md` for complete checklist.

**Quick Validation:**
1. ✅ Ingress/TLS configured correctly
2. ✅ Redirect URI matches exactly
3. ✅ IdP issuer reachable
4. ✅ Client credentials valid
5. ✅ Role mapping configured
6. ✅ Login flow works end-to-end
7. ✅ Logout works
8. ✅ Session invalidation works

#### Failure Drills

**Purpose:** Understand failure modes and recovery procedures.

**Drill 1: Redirect URI Mismatch**
- **Change:** Modify redirect URI in Helm values (add trailing slash)
- **Observe:** Login redirect fails
- **Recover:** Revert change, restart pods
- **Validate:** Login works again

**Drill 2: Missing Claim**
- **Change:** Remove `groups` claim from IdP configuration
- **Observe:** Users authenticate but have no role
- **Recover:** Restore `groups` claim
- **Validate:** Role mapping works again

**Drill 3: Secret Rotation Wrong**
- **Change:** Update client secret in IdP but not in LangSmith
- **Observe:** Authentication fails with "invalid client"
- **Recover:** Update Kubernetes secret, restart pods
- **Validate:** Authentication works again

**Note:** These drills are **optional** and should only be run in non-production environments.

---

## Common Pitfalls

### Login Loop
**Symptom:** User redirected to IdP, then back to LangSmith, then to IdP again (infinite loop)

**Causes:**
- Redirect URI mismatch
- Session cookie not set (TLS/cookie issues)
- Token validation failure

**Fix:** Check redirect URI exactness, verify TLS certificate, check token validation logs

### No Data After Login
**Symptom:** User authenticates successfully but sees empty workspace

**Causes:**
- Role mapping not configured
- User not in any mapped groups
- Workspace not assigned to user's organization

**Fix:** Verify role mapping configuration, check user's group membership, verify workspace assignment

### TLS Callback Issues
**Symptom:** IdP callback fails with TLS errors

**Causes:**
- Self-signed certificate on LangSmith domain
- Certificate chain incomplete
- Certificate expired

**Fix:** Use valid TLS certificate from trusted CA, ensure full chain is present

### Multiple IdPs
**Symptom:** Confusion about which IdP to use

**Causes:**
- Multiple IdP configurations present
- Configuration precedence unclear

**Fix:** Use single IdP configuration, remove unused configurations

---

## Security & Compliance Callouts

### Least Privilege
- Start with minimal admin access
- Use group-based role mapping
- Regular access reviews
- Document all admin assignments

### Auditability
- All authentication events logged
- Role changes tracked
- Session creation/destruction logged
- Export logs to SIEM for compliance

### Centralized Identity Governance
- Manage users in IdP, not LangSmith
- Use IdP groups for access control
- Regular access reviews in IdP
- Deprovision users in IdP when they leave

---

## Artifacts Participants Leave With

1. **SSO Configuration**
   - Helm values file with auth configuration
   - Kubernetes secrets for client credentials
   - Documentation of IdP settings

2. **IdP Settings Document**
   - Redirect URI whitelisted
   - Required claims configured
   - Scopes configured
   - Group structure documented

3. **Mapping Reference**
   - Group-to-role mapping table
   - Admin assignments documented
   - Workspace access rules

4. **Validation Checklist**
   - Completed validation checklist
   - Test results for admin and standard user
   - Logout/session invalidation verified

5. **Debugging Playbook**
   - Troubleshooting guide reference
   - Log locations documented
   - Support bundle procedure

---

## Next Steps

1. **Run the validation notebook:**
   - `notebooks/module-2/01_sso_oidc_validation.ipynb` (OIDC)
   - `notebooks/module-2/02_sso_saml_validation.ipynb` (SAML)

2. **Complete the validation checklist:**
   - `docs/shared/auth_validation_checklist.md`

3. **Review troubleshooting guide:**
   - `docs/shared/auth_troubleshooting.md`

4. **Proceed to Module 3** (if applicable)

---

## References

- [OIDC Specification](https://openid.net/specs/openid-connect-core-1_0.html)
- [SAML 2.0 Specification](http://docs.oasis-open.org/security/saml/v2.0/)
- LangSmith Helm Chart Documentation
- Your IdP's OIDC/SAML documentation

