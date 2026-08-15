FROM python:3.12-slim

# Install Android SDK build-tools (aapt2, apksigner) and Java JRE
RUN apt-get update && apt-get install -y --no-install-recommends \
    openjdk-17-jre-headless \
    unzip \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Download Android SDK build-tools and platform
ENV ANDROID_HOME=/opt/android-sdk
RUN mkdir -p ${ANDROID_HOME}/build-tools/34.0.0 \
    ${ANDROID_HOME}/platforms/android-34 \
    && wget -q https://dl.google.com/android/repository/build-tools_r34-linux.zip -O /tmp/bt.zip \
    && unzip -q /tmp/bt.zip -d /tmp/bt \
    && mv /tmp/bt/android-14/* ${ANDROID_HOME}/build-tools/34.0.0/ \
    && wget -q https://dl.google.com/android/repository/platform-34-ext7_r02.zip -O /tmp/platform.zip \
    && unzip -q /tmp/platform.zip -d /tmp/platform \
    && mv /tmp/platform/android-14/* ${ANDROID_HOME}/platforms/android-34/ \
    && rm -rf /tmp/bt.zip /tmp/bt /tmp/platform.zip /tmp/platform

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV ANDROID_HOME=/opt/android-sdk
ENV PATH="${ANDROID_HOME}/build-tools/34.0.0:${PATH}"

EXPOSE 8000

CMD ["uvicorn", "api.app:app", "--host", "0.0.0.0", "--port", "8000"]
