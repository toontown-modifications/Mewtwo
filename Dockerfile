FROM quay.io/rocketprogrammer/panda3d:main

# Migrate all files into root
WORKDIR /Mewtwo
COPY ./ .

# Install all pip requirements
RUN pip install -r requirements.txt

# Install all the required files from the repository
RUN apt update
RUN apt install -y screen

CMD [ "/bin/bash", "entrypoint.sh" ]