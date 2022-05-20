FROM ubuntu:20.04

# docker build -t s2_download:v1.0 .

ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8

RUN apt-get update && DEBIAN_FRONTEND="noninteractive" TZ="Europe/Paris" apt-get install -y tzdata

RUN apt-get update && \
    apt-get install -y apt-utils && \
    apt-get install -y python3 && \
    apt-get install -y curl

RUN apt-get install gdal-bin libgdal-dev libspatialindex-dev python3-pip -y 

RUN pip3 install geopandas rtree shapely datetime pandas

RUN pip3 install rasterio numpy

COPY . /opt/task/

ENTRYPOINT ["python3", "/opt/task/s2_download.py"]
