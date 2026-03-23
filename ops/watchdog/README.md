# Watchdog

Bridge keeps falling over due to networking errors stopping it reaching IMDS and thus ens5.

Install on the instance:

```bash
sudo install -m 0755 ops/watchdog/bridge-watchdog.sh /usr/local/bin/bridge-watchdog.sh
sudo install -m 0644 ops/watchdog/bridge-watchdog.service /etc/systemd/system/bridge-watchdog.service
sudo install -m 0644 ops/watchdog/bridge-watchdog.timer /etc/systemd/system/bridge-watchdog.timer
sudo systemctl daemon-reload
sudo systemctl enable --now bridge-watchdog.timer
```

Defaults:

- check IMDS and `http://127.0.0.1/` every minute
- restart `systemd-networkd` after 5 failed minutes
- reboot after 10 failed minutes
