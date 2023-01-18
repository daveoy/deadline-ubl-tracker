FROM python:3.11.1
RUN pip install prometheus_client requests
COPY license-counts.py .
CMD python  ./license-counts.py