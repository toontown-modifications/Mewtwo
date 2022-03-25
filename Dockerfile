FROM ubuntu:20.04

# Extend the system environments
ENV LD_LIBRARY_PATH /lib:/usr/lib:/usr/local/lib
ENV DEBIAN_FRONTEND=noninteractive

# Install all the required files from the repository
RUN apt update
RUN apt install -y build-essential curl wget git python3 python3-distutils python3-apt libassimp5 libavcodec58 libavformat58 libavutil56 libbullet2.88 libcg libcggl libegl1 libfreetype6 libgl1 libgles1 libgles2 libharfbuzz0b libjpeg8 libode8 libopenal1 libopenexr24 libopusfile0 libpng16-16 libswresample3 libswscale5 libtiff5 libvorbisfile3 nvidia-cg-toolkit libmysqlclient-dev python3-dev screen libfftw3-dev libuv1-dev
RUN apt install -y neofetch htop nano software-properties-common psmisc
RUN add-apt-repository ppa:deadsnakes/ppa && apt update
RUN apt install -y python3.9

# Install pip
RUN curl -s -L https://bootstrap.pypa.io/get-pip.py | python3

# Grab Panda3D and the older FSM module & modified DistributedObjectAI.
RUN wget -P /panda3d https://rocketprogrammer.me/linux/py3_a.deb
RUN wget -P /panda3d https://rocketprogrammer.me/binaries/FSM.py
RUN wget -P /panda3d https://rocketprogrammer.me/binaries/DistributedObjectAI.py

# Install panda3d & apply our changes
RUN cd /panda3d \
    && dpkg -i py3_a.deb
RUN cd /panda3d && cp FSM.py /usr/share/panda3d/direct/fsm/FSM.py
RUN cd /panda3d && cp DistributedObjectAI.py /usr/share/panda3d/direct/distributed/DistributedObjectAI.py

# Copy all files into Docker image
COPY . /server
WORKDIR /server

RUN git clone https://oauth2:NBSQjuVLzk3XkAxAPTuj@gitlab.com/SunriseMMOs/stunnel /stunnel
RUN git clone https://oauth2:NBSQjuVLzk3XkAxAPTuj@gitlab.com/SunriseMMOs/discord-status-bot /discord-status-bot

# Install the Discord bot's dependencies
RUN cd /discord-status-bot && python3 -m pip install -r requirements.txt

# Install pip dependencies
RUN pip install -r requirements.txt

# Run the server
CMD chmod +x ./entrypoint.sh && ./entrypoint.sh