"""Package-repo URI helper (Phase 4+).

No use_internal_rpm_apt_repo mode enum. Prefer explicit pkg_repo_base (repository root),
else pkg_repo_nginx_ingress_domain (nginx mirror host baking), else public URL.
"""

from __future__ import annotations

import re

_PUBLIC_BY_SLUG = {
    "debian-main": "https://deb.debian.org/debian",
    "debian-security": "https://deb.debian.org/debian-security",
    "debian-non-free": "https://deb.debian.org/debian",
    "ubuntu": "https://archive.ubuntu.com/ubuntu",
    "pgdg-apt": "https://apt.postgresql.org/pub/repos/apt",
    "pgdg-yum": "https://download.postgresql.org/pub/repos/yum",
    "debian-containerd": "https://download.docker.com/linux/debian",
    "ubuntu-containerd": "https://download.docker.com/linux/ubuntu",
    "yum_docker-ce-stable-9": "https://download.docker.com/linux/centos/9/x86_64/stable",
    "yum_docker-ce-stable-10": "https://download.docker.com/linux/centos/10/x86_64/stable",
}


def _slug_host(value):
    slug = re.sub(r"[^a-zA-Z0-9._-]", "-", value or "")
    return slug.replace(".", "-")


def _public_uri(slug, pkg_repo_upstreams):
    for item in pkg_repo_upstreams or []:
        if item.get("slug") == slug:
            url = (item.get("upstream_url") or "").rstrip("/")
            if url:
                return url
    if re.fullmatch(r"k8s-ubuntu-\d+\.\d+", slug or ""):
        ver = slug.split("k8s-ubuntu-", 1)[1]
        return "https://pkgs.k8s.io/core:/stable:/v{}/deb/".format(ver)
    if re.fullmatch(r"k8s-\d+\.\d+", slug or ""):
        ver = slug.split("k8s-", 1)[1]
        return "https://pkgs.k8s.io/core:/stable:/v{}/rpm/".format(ver)
    return _PUBLIC_BY_SLUG.get(slug, "")


def pkg_repo_uri(
    slug,
    pkg_repo_base="",
    pkg_repo_nginx_ingress_domain="",
    pkg_repo_upstreams=None,
):
    """Resolve a catalog slug to the URI apt/yum should use."""
    slug = slug or ""
    public = _public_uri(slug, pkg_repo_upstreams)
    base = (pkg_repo_base or "").rstrip("/")
    if base:
        return "{}/{}".format(base, slug)
    domain = (pkg_repo_nginx_ingress_domain or "").strip()
    if domain:
        return "https://{}.{}".format(_slug_host(slug), domain)
    return public


class FilterModule(object):
    def filters(self):
        return {
            "pkg_repo_uri": pkg_repo_uri,
        }
