"""Containerd registry mirror endpoints (must match infra registry proxy hostnames).

Keep slug rules in sync with atlas-infra-edge/filter_plugins/registry_mirror.py.
"""

import re

_VALID_UPSTREAM = re.compile(r"^https://[^/]*\.[^/]+/?$")


def _slug(dir_name):
    slug = re.sub(r"[^a-zA-Z0-9._-]", "-", dir_name or "")
    return slug.replace(".", "-")


def _registry_slug(item):
    server = (item or {}).get("server", "")
    dir_name = (item or {}).get("dir_name", "")
    mirror_path = (item or {}).get("mirror_path") or ""
    if _VALID_UPSTREAM.match(server):
        # Vanity registries (reg.kyverno.io → ghcr.io, cr.fluentbit.io → docker.io)
        # share the pull-through of mirror_path. Do not slug dir_name — that vhost
        # is never created.
        if "." in mirror_path and mirror_path != dir_name:
            return _slug(mirror_path)
        return _slug(dir_name)
    if mirror_path == "docker-hub":
        return "docker-io"
    return _slug(dir_name)


class FilterModule(object):
    def filters(self):
        return {
            "containerd_mirror_endpoint": self.containerd_mirror_endpoint,
        }

    def containerd_mirror_endpoint(self, item, registry_ingress_domain):
        slug = _registry_slug(item)
        return f"https://{slug}.{registry_ingress_domain}"
