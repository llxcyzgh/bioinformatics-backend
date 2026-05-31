#!/bin/bash
set -e

cd /opt/sge
./install.sh

source /opt/sge/default/common/settings.sh

# Fix min_gid to 0 so root can submit jobs (default template sets it to 100, blocks root gid=0)
# Directly patch the spool configuration file
CONFIG_FILE="/opt/sge/default/spool/master/configuration"
if [ -f "$CONFIG_FILE" ]; then
    sed -i 's/min_gid.*/min_gid                      0/' "$CONFIG_FILE"
fi

# Restart qmaster to pick up config change
/opt/sge/default/common/sgemaster stop
sleep 2
/opt/sge/default/common/sgemaster start
sleep 2

# Clear any queue error state
qmod -cq all.q 2>/dev/null || true
qmod -e all.q@docker 2>/dev/null || true

# Health check job
echo '#!/bin/bash
echo "SGE health check passed"
hostname
date' > /tmp/healthcheck.sh
chmod +x /tmp/healthcheck.sh
qsub -N healthcheck /tmp/healthcheck.sh

sleep 8

echo ""
echo "=== SGE Status ==="
ps aux | grep sge_ | grep -v grep || true
echo ""
qstat -f
echo ""
echo "=== Health Check ==="
cat /root/healthcheck.o* 2>/dev/null || echo "(pending)"
echo ""
echo "SGE ready. Submit via: docker exec sge-master bash -c 'source /opt/sge/default/common/settings.sh && qsub ...'"
echo "Shared volume: /shared"

sleep infinity
