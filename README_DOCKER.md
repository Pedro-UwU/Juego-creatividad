# 🐳 Docker Instructions

## Build the image

```bash
docker build -t my-app .
```

## Run the container

Replace `<YOUR_HOST_LAN_IP>` with your actual LAN IP address (e.g. 192.168.1.42):

```bash
docker run --rm \
  -e HOST_LAN_IP=<YOUR_HOST_LAN_IP> \
  -p 8000:8000 \
  my-app
```

## Notes

- `HOST_LAN_IP` is used to generate a QR code pointing to your machine’s LAN IP.
- Make sure port `8000` is open and accessible on your local network.

