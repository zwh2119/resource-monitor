import time
import iperf3
import psutil
import threading

import eventlet

from log import LOGGER
from client import http_request

interval = 3
iperf3_ports = [5201, 5202]
iperf3_server = False
iperf3_port = 5201

iperf3_server_ip = '114.212.81.11'

def iperf_server(port):
    server = iperf3.Server()
    server.port = port
    print('Running server: {0}:{1}'.format(server.bind_address, server.port))

    while True:
        try:
            result = server.run()
        except Exception as e:
            continue

        if result.error:
            print(result.error)
        else:
            print('')
            print('Test results from {0}:{1}'.format(result.remote_host,
                                                     result.remote_port))
            print('  started at         {0}'.format(result.time))
            print('  bytes received     {0}'.format(result.received_bytes))

            print('Average transmitted received in all sorts of networky formats:')
            print('  bits per second      (bps)   {0}'.format(result.received_bps))
            print('  Kilobits per second  (kbps)  {0}'.format(result.received_kbps))
            print('  Megabits per second  (Mbps)  {0}'.format(result.received_Mbps))
            print('  KiloBytes per second (kB/s)  {0}'.format(result.received_kB_s))
            print('  MegaBytes per second (MB/s)  {0}'.format(result.received_MB_s))
            print('')


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
                threading.Thread(target=self.get_total_bandwidth)
            ]
            for thread in threads:
                thread.start()

            # wait for all thread complete
            for thread in threads:
                thread.join()

            data = {'cpu': self.cpu, 'memory': self.mem, 'bandwidth': self.bandwidth,
                    'total_bandwidth': self.total_bandwidth, 'is_server': iperf3_server}

            print(data)

            # TODO: post resource to scheduler

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

        print('Connecting to {0}:{1}'.format(client.server_hostname, client.port))
        result = client.run()

        if result.error:
            print(result.error)
        else:
            print('')
            print('Test completed:')
            print('  started at         {0}'.format(result.time))
            print('  bytes transmitted  {0}'.format(result.sent_bytes))
            print('  retransmits        {0}'.format(result.retransmits))
            print('  avg cpu load       {0}%\n'.format(result.local_cpu_total))

            print('Average transmitted data in all sorts of networky formats:')
            print('  bits per second      (bps)   {0}'.format(result.sent_bps))
            print('  Kilobits per second  (kbps)  {0}'.format(result.sent_kbps))
            print('  Megabits per second  (Mbps)  {0}'.format(result.sent_Mbps))
            print('  KiloBytes per second (kB/s)  {0}'.format(result.sent_kB_s))
            print('  MegaBytes per second (MB/s)  {0}'.format(result.sent_MB_s))

        self.bandwidth = result.sent_Mbps

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
