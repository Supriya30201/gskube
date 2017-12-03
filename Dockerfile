FROM ubuntu:14.04
MAINTAINER Sanket Modi "sanket.modi@gslab.com"
RUN apt-get update && apt-get -y upgrade
RUN apt-get install -y python
RUN apt-get install -y git
RUN git clone http://sanket.modi:@gitlab/sanket.modi/ServiceOnline.git