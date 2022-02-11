FROM python:3.9.6

WORKDIR /usr/src/app

# For safety reason, create an user with lower privileges than root and run from there
RUN useradd -m -d /home/doombot -s /bin/bash doombot && \
    mkdir /usr/src/doombot && \
    chown -R doombot /usr/src/doombot

USER doombot

COPY requirements.txt ./
RUN pip3 install --no-warn-script-location --no-cache-dir -r requirements.txt

COPY . .

CMD [ "python3", "main.py" ]