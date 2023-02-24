### Ping with Python and asyncio

This script uses the ping subprocess. Modify the values in settings.py:

CONCURRENT_TASKS: number of ping processes opened at the same time
NETWORKS: networks to validate in 'network/mask' format

The number of CONCURRENT_TASKS depends on performance of the machine and network connection

Run the script

```bash
python async.py
```
