FROM ubuntu:22.04
ENV DEBIAN_FRONTEND=noninteractive

ARG PUID=err
ARG PGID=err

ENV PUID=${PUID}
ENV PGID=${PGID}

RUN apt-get update && apt-get install -y \
    gosu \
    sudo \
    python3 \
    python3-tk \
    python3-yaml \
    ansible \
    dbus-x11 \
    fonts-noto-color-emoji \
    x11-xserver-utils \
    pulseaudio-utils \
    && rm -rf /var/lib/apt/lists/*

COPY config.yaml /build/config.yaml
COPY apps/ /apps/
COPY utils/build.py /build/build.py
COPY utils/startup.py /build/startup.py

RUN mkdir -p /opt/launcher/apps
COPY utils/launcher.py /opt/launcher/launcher.py

RUN python3 /build/build.py

COPY utils/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
CMD ["python3", "/opt/launcher/launcher.py"]