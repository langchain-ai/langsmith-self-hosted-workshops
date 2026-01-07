# Authentication Validation Checklist

**Purpose:** Operator-friendly checklist for validating SSO configuration  
**Use:** Complete this checklist after running the validation notebook(s)

---

## Preconditions

- [ ] DNS configured and resolving correctly
- [ ] TLS certificate valid and trusted (not self-signed in production)
- [ ] Ingress configured and accessible
- [ ] LangSmith deployment healthy (all pods running, PVCs bound)

---

## Configuration Inputs

### OIDC Configuration
- [ ] `OIDC_ISSUER` set and accessible
- [ ] `OIDC_CLIENT_ID` set
- [ ] `OIDC_CLIENT_SECRET` set (stored in Kubernetes secret)
- [ ] `OIDC_REDIRECT_URI` matches exactly between LangSmith and IdP
- [ ] `OIDC_SCOPES` includes `openid` and `email`
- [ ] `OIDC_SCOPES` includes `groups` (if using group-based role mapping)

### SAML Configuration
- [ ] `SAML_METADATA_URL` accessible OR `SAML_METADATA_FILE` exists
- [ ] SAML metadata XML is valid
- [ ] Entity ID matches between LangSmith and IdP
- [ ] Signing certificate present in metadata
- [ ] SSO endpoints found in metadata

### Common to Both
- [ ] `LANGSMITH_DOMAIN` matches actual domain
- [ ] Claim/attribute mappings configured
- [ ] Role mapping configured (groups or users)

---

## Role Mapping

- [ ] Group-to-role mapping configured (preferred)
- [ ] Admin groups identified and mapped
- [ ] Member groups identified and mapped
- [ ] Viewer groups identified and mapped (if applicable)
- [ ] Minimal admin principle followed (1-2 admins to start)

---

## Login Validation

### Admin User
- [ ] Admin user can log in via SSO
- [ ] Admin user sees correct role (admin)
- [ ] Admin user can access organization settings
- [ ] Admin user can manage workspaces
- [ ] Admin user can manage users (if applicable)

### Standard User
- [ ] Standard user can log in via SSO
- [ ] Standard user sees correct role (member/viewer)
- [ ] Standard user can access assigned workspaces
- [ ] Standard user cannot access organization settings
- [ ] Standard user cannot manage users

---

## Session Management

- [ ] Logout works correctly
- [ ] Session invalidation works (logout from IdP invalidates LangSmith session)
- [ ] Session timeout configured appropriately
- [ ] Multiple browser sessions work independently

---

## Audit Evidence

- [ ] Authentication events logged
- [ ] Role assignments logged
- [ ] Session creation/destruction logged
- [ ] Failed authentication attempts logged
- [ ] Logs exportable to SIEM (if required)

---

## Documentation

- [ ] Helm values file saved (with secrets redacted)
- [ ] IdP settings documented
- [ ] Group-to-role mapping table created
- [ ] Admin assignments documented
- [ ] Troubleshooting playbook bookmarked

---

## Sign-Off

**Validated by:** _________________  
**Date:** _________________  
**Notes:** _________________

---

**Next Steps:**
- Proceed to Module 3 (if applicable)
- Schedule regular access reviews
- Document any deviations from standard configuration

