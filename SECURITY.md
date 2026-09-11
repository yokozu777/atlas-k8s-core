# Security

## Reporting

If you discover a security issue in this repository, please open a private report with the maintainers (do not file a public issue with exploit details or credentials).

## Secrets in this repo

Do **not** commit:

- real registry / pullsecret credentials
- cluster kubeconfigs with client keys
- SSH private keys
- deprecated monolithic `secrets.yml` / `*.vault` with live values
- live inventory with production hosts (`inventory.yml`, local `hosts`)

Prefer `group_vars/all/atlas-k8s-core.secrets.yml` with Ansible Vault (trackable; do **not** gitignore). Standalone operators may also use `EXTRA_VARS_FILE` / `examples/secrets.example.yml` **outside** the tree. A monolithic `secrets.yml` is deprecated and must not hold live credentials in git.


Tracked examples must use inert placeholders only (see `docs/examples/example_pullsecret.yaml`).

## Git history note (pre-publish)

Older commits (including the current tree until scrubbed) embedded a **real Nexus registry password** inside a dockerconfig pullsecret example:

`docs/examples/example_pullsecret.yaml` — `.dockerconfigjson` for `nexus.mxhash.com` / user `admin` / lab password matching the org `Welcomeback…` pattern (base64).

(Introduced in commit `408e174` / “init atlas”; the blob remains reachable in git history even after the working tree is replaced with placeholders.)

Product sources (`roles/`, `playbooks/`, `group_vars/`, examples, inventory example, runner) must stay free of org hostnames and lab credentials. Lab overlays belong in the orchestrator inventory, not in this repository’s defaults.

Before making this repository public:

1. **Rotate / revoke** that Nexus (and any reused) password / token.
2. Rewrite history (`git filter-repo` / BFG) to purge the blob, or publish from a fresh orphan branch that contains only the cleaned tree.
3. Assume the credential is compromised for as long as those commits remain reachable on any remote.
