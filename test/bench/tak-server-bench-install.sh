#!/bin/bash
# Install the official TAK Server on a bench Pi for evaluation. Run as root.
#
#   tak-server-bench-install.sh own-ca
#   tak-server-bench-install.sh staged-bundle BUNDLE.tgz
#
# Environment: TAK_DEB (path to the takserver .deb, obtained by the operator
# from tak.gov under its terms; never committed here) and TAK_DEB_SHA256 (its
# expected hash, checked before anything is installed).
#
# EVALUATION ONLY. FML-ADR-032 prefers OpenTAKServer; this exists to measure an
# alternative under that ADR's fallback, not to change the baseline. See
# docs/evidence/TBR-COMP-01/ and docs/evidence/TBR-HA-01/.
#
# own-ca         makes a bench CA, a server certificate, and admin and two client
#                certificates with placeholder subjects (no real location).
# staged-bundle  uses a server keystore issued by ANOTHER node's bench CA plus that
#                CA's trust store, so two servers share one trust anchor (CONOPS
#                25.3, SAD 11.3). The CA's private key never leaves the CA node.
#                The bundle holds: takserver-b.jks, truststore-root.jks, ca.pem,
#                admin.pem.
#
# Debian 13 (trixie) carries neither openjdk-17 nor PostgreSQL 18, which the
# package Depends on, so this adds the vendors' own repositories (Adoptium,
# PGDG) and satisfies the openjdk-17-jdk dependency with a local equivs shim
# that depends on temurin-17-jdk, which keeps apt consistent.
#
# Two defects found on the first run are fixed here and recorded in the
# evidence: a umask set for the secrets file leaked onto CoreConfig.xml (the
# config service then could not read it), and the package's postinst may
# create the database role with its own password, which the setup script
# then leaves unchanged; the role is aligned explicitly.
set -euo pipefail
MODE=${1:?usage: tak-server-bench-install.sh own-ca | staged-bundle BUNDLE.tgz}
BUNDLE=${2:-}
DEB=${TAK_DEB:?set TAK_DEB to the takserver .deb}
SUM=${TAK_DEB_SHA256:?set TAK_DEB_SHA256 to its expected sha256}
LOG=/var/log/fml-takserver-install.log
SECRETS=/root/fml-takserver-bench.secrets
exec > >(tee -a "$LOG") 2>&1
export DEBIAN_FRONTEND=noninteractive
step() {
  echo
  echo "== $(date +%T) $*"
}
[ "$(id -u)" -eq 0 ] || {
  echo "FAIL: run as root"
  exit 1
}
case "$MODE" in
  own-ca) ;;
  staged-bundle) [ -s "$BUNDLE" ] || {
    echo "FAIL: bundle not found"
    exit 1
  } ;;
  *)
    echo "FAIL: unknown mode $MODE"
    exit 64
    ;;
esac

step "preflight"
echo "$SUM  $DEB" | sha256sum -c -
for p in 8089 8443 8446 5432; do
  ss -ltnH "( sport = :$p )" | grep -q . && {
    echo "FAIL: port $p already in use"
    exit 1
  }
done

step "vendor repositories: Adoptium (Temurin 17) and PostgreSQL (18 + PostGIS)"
apt-get update -q
apt-get install -y -q ca-certificates curl gpg equivs
curl -fsSL https://packages.adoptium.net/artifactory/api/gpg/key/public |
  gpg --dearmor --yes -o /usr/share/keyrings/adoptium.gpg
echo "deb [signed-by=/usr/share/keyrings/adoptium.gpg] https://packages.adoptium.net/artifactory/deb trixie main" \
  >/etc/apt/sources.list.d/adoptium.list
curl -fsSL https://www.postgresql.org/media/keys/ACCC4CF8.asc |
  gpg --dearmor --yes -o /usr/share/keyrings/pgdg.gpg
echo "deb [signed-by=/usr/share/keyrings/pgdg.gpg] https://apt.postgresql.org/pub/repos/apt trixie-pgdg main" \
  >/etc/apt/sources.list.d/pgdg.list
gpg --show-keys --with-fingerprint /usr/share/keyrings/adoptium.gpg /usr/share/keyrings/pgdg.gpg 2>/dev/null |
  grep -E "^ +[0-9A-F ]{40,}|^uid"
apt-get update -q
apt-get install -y -q temurin-17-jdk postgresql-18 postgresql-18-postgis-3 openssl bc

step "shim: satisfy takserver's openjdk-17-jdk dependency with Temurin 17"
if ! dpkg -s openjdk-17-jdk >/dev/null 2>&1; then
  W=$(mktemp -d)
  cat >"$W/shim" <<'E'
Section: misc
Priority: optional
Standards-Version: 3.9.2
Package: openjdk-17-jdk
Version: 17.0.0~fml-shim1
Depends: temurin-17-jdk
Description: FML bench shim satisfying takserver's openjdk-17-jdk dependency with Temurin 17
E
  (cd "$W" && equivs-build shim >/dev/null && dpkg -i openjdk-17-jdk_*.deb)
fi

step "install takserver package"
apt-get install -y -q "$DEB" </dev/null || true
dpkg -s takserver | grep -E "^(Status|Version)"

step "database: generated password, schema, role aligned"
if [ ! -s "$SECRETS" ]; then
  (
    umask 077
    {
      echo "DB_PASS=$(openssl rand -hex 16)"
      echo "CAPASS=atakatak  # TAK default; bench only, never ship"
    } >"$SECRETS"
  )
fi
DB_PASS=$(sed -n 's/^DB_PASS=//p' "$SECRETS")
systemctl enable --now postgresql
envpass="$DB_PASS" /opt/tak/db-utils/takserver-setup-db.sh </dev/null || true
[ -f /opt/tak/CoreConfig.xml ] || cp /opt/tak/CoreConfig.example.xml /opt/tak/CoreConfig.xml
sed -i -E "/<connection url=\"jdbc:postgresql/ s/password=\"[^\"]*\"/password=\"$DB_PASS\"/" /opt/tak/CoreConfig.xml
chown tak:tak /opt/tak/CoreConfig.xml && chmod 600 /opt/tak/CoreConfig.xml
su - postgres -c "psql -q -v ON_ERROR_STOP=1 -d cot" <<SQL
ALTER ROLE martiuser WITH PASSWORD '$DB_PASS';
SQL

step "certificates ($MODE; placeholder subjects, no real location)"
cd /opt/tak/certs
if [ "$MODE" = own-ca ]; then
  export STATE=XX CITY=Bench ORGANIZATIONAL_UNIT=FML-Bench ORGANIZATION=FML
  if [ ! -f files/ca.pem ]; then
    ./makeRootCa.sh --ca-name FML-BENCH-TAK-CA </dev/null
    ./makeCert.sh server takserver </dev/null
    for c in admin wintak-bench itak-bench; do ./makeCert.sh client "$c" </dev/null; done
  fi
else
  install -d -o tak -g tak -m 750 files
  tar -xzf "$BUNDLE" -C files
  mv -f files/takserver-b.jks files/takserver.jks
  cp -f files/truststore-root.jks files/fed-truststore.jks
fi
chown -R tak:tak files
for f in files/*.p12 files/*.jks files/*.pem; do [ -e "$f" ] && printf '%s ' "${f#files/}"; done
echo

step "start (about ten minutes on a Pi 4 held at 600 MHz)"
systemctl daemon-reload
systemctl enable takserver
systemctl restart takserver
for _ in $(seq 1 90); do
  ss -ltnH "( sport = :8443 )" | grep -q . && break
  sleep 10
done
ss -ltnH | awk '{print $4}' | grep -E ":(8089|8443|8446)$" || echo "WARN: TAK ports not listening yet"
java -jar /opt/tak/utils/UserManager.jar certmod -A /opt/tak/certs/files/admin.pem ||
  echo "WARN: admin enable deferred; rerun once the API is up"

step "footprint snapshot (CPU figures untrustworthy while the node is under-voltage)"
vcgencmd get_throttled || true
free -m
ps -eo rss,pcpu,args --sort=-rss | awk 'NR==1 || /java|postgres/' | head -12 | cut -c1-150
echo
echo "== done $(date -Is). Secrets (root only): $SECRETS"
