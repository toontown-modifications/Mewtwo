FROM ubuntu:20.04

# Extend the system environments
ENV LD_LIBRARY_PATH /lib:/usr/lib:/usr/local/lib
ENV DEBIAN_FRONTEND=noninteractive

# Install all the required files from the repository
RUN apt update
RUN apt install -y build-essential curl wget git python3 python3-distutils python3-apt libassimp5 libavcodec58 libavformat58 libavutil56 libbullet2.88 libcg libcggl libegl1 libfreetype6 libgl1 libgles1 libgles2 libharfbuzz0b libjpeg8 libode8 libopenal1 libopenexr24 libopusfile0 libpng16-16 libswresample3 libswscale5 libtiff5 libvorbisfile3 nvidia-cg-toolkit libmysqlclient-dev python3-dev screen libfftw3-dev libuv1-dev

# Install pip
RUN curl -s -L https://bootstrap.pypa.io/get-pip.py | python3

# Grab Panda3D and the older FSM module.
RUN wget -P /panda3d https://rocketprogrammer.me/linux/py3_a.deb
RUN wget -P /panda3d https://rocketprogrammer.me/binaries/FSM.py

# Install panda3d
RUN cd /panda3d \
    && dpkg -i py3_a.deb
RUN cd /panda3d && cp FSM.py /usr/share/panda3d/direct/fsm/FSM.py

# Migrate all files into root
WORKDIR /server
RUN git clone https://Robot:ce11d5d015c990243b496e7babe5bdfe3c8f0bd9@git.sunrise.games/SunriseGames/Mewtwo.git /server
COPY ./ .

# Install pip dependencies
RUN pip install -r requirements.txt

# Run the server
CMD chmod +x ./game/entrypoint.sh && ./game/entrypoint.sh