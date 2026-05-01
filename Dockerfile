FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y \
    wget curl bzip2 xz-utils gosu \
    libgtk-3-0 libdbus-glib-1-2 \
    libasound2 libx11-xcb1 libxtst6 \
    fonts-liberation ca-certificates \
    libcap2-bin \
    libpci3 \
    libegl1 \
    libgl1-mesa-glx \
    libgl1 \
    dbus-x11 \
    libcanberra-gtk3-module \
    pciutils \
    python3 \
    python3-tk \
    && rm -rf /var/lib/apt/lists/*

RUN wget -q "https://www.zotero.org/download/client/dl?channel=release&platform=linux-x86_64" \
    -O /tmp/zotero.tar.xz \
    && tar -xJf /tmp/zotero.tar.xz -C /opt \
    && mv /opt/Zotero_linux-x86_64 /opt/zotero \
    && rm /tmp/zotero.tar.xz

RUN chmod u+s /opt/zotero/zotero-sandbox 2>/dev/null || true

RUN mkdir -p /zotero-data /opt/launcher

COPY launcher.py /opt/launcher/launcher.py
COPY launcher.sh /launcher.sh
RUN chmod +x /launcher.sh

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
CMD ["/launcher.sh"]