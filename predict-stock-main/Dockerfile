FROM python:3.9

LABEL maintainer="l101871891@gmail.com"

COPY . /app/server

WORKDIR /app/server

RUN pip3 install -r requirements.txt
RUN apt-get update && \
apt-get install -y sudo curl git && \
curl -s https://packagecloud.io/install/repositories/github/git-lfs/script.deb.sh | sudo bash && \
sudo apt-get install git-lfs
RUN git lfs pull --include="weights_h5/weights.h5"
RUN git lfs pull --include="weights_h5/weights2.h5"
RUN git lfs pull --include="weights_h5/weights3.h5"

ENTRYPOINT ["python", "index.py"]
