FROM quay.io/rocketprogrammer/panda3d:main

# Migrate all files into root
WORKDIR /Mewtwo
COPY ./ .

# Install all pip requirements
RUN pip install -r requirements.txt

CMD [ "/bin/bash", "entrypoint.sh" ]