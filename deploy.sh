DEBIAN_FRONTEND=noninteractive apt-get update && apt-get install -y --no-install-recommends \
curl \
build-essential \
libpq-dev \
&& rm -rf /var/lib/apt/lists/*

pip install -r requirements.txt