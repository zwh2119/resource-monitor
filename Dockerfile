FROM python:3.6
MAINTAINER Wenhui Zhou

RUN apt-get update && apt-get install -y iperf3

COPY ./requirements.txt ./
RUN pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

COPY . .

CMD ["python3", "monitor_server.py"]