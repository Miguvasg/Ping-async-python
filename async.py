import os
import time
import ipaddress
import asyncio
from functools import wraps
import pandas as pd
from settings import CONCURRENT_TASKS, NETWORKS


# wait_resources is to limit the number of processes at a time, since if it is 
# not limited, an OSError appears for the number of open files when there are 
# many NETWORKS to be validated
def wait_resources(concurrent_tasks=1):
    semaphore = asyncio.Semaphore(concurrent_tasks)
    def wrapper(function):
        @wraps(function)
        async def inside_function(*args, **kwargs):
            async with semaphore:
                return await function(*args, **kwargs)
        return inside_function
    return wrapper


@wait_resources(concurrent_tasks=CONCURRENT_TASKS)
async def aping(ip, count=3, wait_sec=1):
    cmd = f'ping -c {count} -W {wait_sec} {ip}'
    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await proc.communicate()
    if proc.returncode:
        return None
    if stdout:
        output = [line for line in f'{stdout.decode()}'.split("\n") if line != '']
    else:
        output = [line for line in f'{stderr.decode()}'.split("\n") if line != '']
    total = output[-2].split(',')[3].split()[1]
    loss = output[-2].split(',')[2].split()[0]
    timing = output[-1].split()[3].split('/')
    return {
        'type': 'rtt',
        'min': timing[0],
        'avg': timing[1],
        'max': timing[2],
        'mdev': timing[3],
        'total': total,
        'loss': loss,
    }


async def main():
    results = {}
    ips_to_validate = (
        ip.compressed for network in NETWORKS
        for ip in ipaddress.ip_network(network).hosts()
    )
    asyncio_tasks = [
        asyncio.create_task(aping(ip), name=ip) for ip in ips_to_validate
    ]
    for task in asyncio_tasks:
        await task
        if task.result() is not None:
            results[task.get_name()] = task.result()
    print(results)
    print(f'equipos arriba: {len(results)}')
    data = pd.DataFrame.from_dict(results, orient='index')
    cont = 0
    while True:
        if cont == 0:
            file_compare = f'tasks_{CONCURRENT_TASKS}.txt'
        else:
            file_compare = f'tasks_{CONCURRENT_TASKS}_{cont}.txt'
        if not os.path.exists(file_compare):
            file_name = file_compare
            break
        cont += 1
    with open(file_name, 'a') as f:
        f.write(data.to_string())


if __name__ == "__main__":
    start = time.perf_counter()
    asyncio.run(main())
    end = time.perf_counter()
    print(f'time: {end - start} seconds')
