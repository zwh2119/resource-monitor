
import time
import iperf3
import psutil
import threading

import eventlet

from log import LOGGER
from client import http_request
from utils import *

interval = 5
iperf3_ports = [5201, 5202]
iperf3_server = False
iperf3_port = 5201

iperf3_server_ip = '114.212.81.11'
scheduler_ip = '114.212.81.11'
scheduler_port = 8140
scheduler_path = 'resource'


def iperf_server(port):
    server = iperf3.Server()
    server.port = port
    LOGGER.debug('Running iperf3 server: {0}:{1}'.format(server.bind_address, server.port))

    while True:
        try:
            result = server.run()
        except Exception as e:
            continue

        if result.error:
            print(result.error)


class MonitorServer:
    def __init__(self):
        self.monitor_interval = interval

        self.cpu = 0
        self.mem = 0
        self.bandwidth = 0
        self.total_bandwidth = 0

        # the first computing of cpu is 0
        self.get_cpu()

        if iperf3_server:
            self.run_iperf_server()

    def run(self):
        while True:
            threads = [
                threading.Thread(target=self.get_cpu),
                threading.Thread(target=self.get_memory),
                threading.Thread(target=self.get_bandwidth),
                # threading.Thread(target=self.get_total_bandwidth)
            ]
            for thread in threads:
                thread.start()

            # wait for all thread complete
            for thread in threads:
                thread.join()

            data = {'cpu': self.cpu, 'memory': self.mem, 'bandwidth': self.bandwidth, 'is_server': iperf3_server}

            LOGGER.debug('resource info:', data)

            resource_post_url = get_merge_address(scheduler_ip, port=scheduler_port, path=scheduler_path)
            http_request(resource_post_url, method='POST', json={'device': get_host_ip(), 'resource': data})

            time.sleep(self.monitor_interval)

    def get_cpu(self):
        self.cpu = psutil.cpu_percent()

    def get_memory(self):
        self.mem = psutil.virtual_memory().percent

    def get_bandwidth(self):

        client = iperf3.Client()
        client.duration = 1
        client.server_hostname = iperf3_server_ip
        client.port = iperf3_port
        client.protocol = 'tcp'

        eventlet.monkey_patch()
        try:
            with eventlet.Timeout(2, True):
                result = client.run()

            if result.error:
                LOGGER.warning('resource monitor iperf3 error:', result.error)

            self.bandwidth = result.sent_Mbps

        except eventlet.timeout.Timeout:
            LOGGER.warning('connect to server timeout!')

    def get_total_bandwidth(self):
        start_upload = psutil.net_io_counters().bytes_sent * 8 / 1024 / 1024
        time.sleep(1)
        end_upload = psutil.net_io_counters().bytes_sent * 8 / 1024 / 1024
        self.total_bandwidth = end_upload - start_upload

    def run_iperf_server(self):
        for port in iperf3_ports:
            threading.Thread(target=iperf_server, args=(port,)).start()


if __name__ == '__main__':
    monitor = MonitorServer()
    monitor.run()
