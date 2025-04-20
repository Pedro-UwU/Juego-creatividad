import qrcode
import socket
import logging
import os
import webbrowser

# Configure logging
logger = logging.getLogger(__name__)


def get_local_ip():
    """Get the local IP address of the machine on the LAN."""
    try:
        # Create a socket that connects to an external server
        # This is a trick to get the local IP address used for external connections
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # It doesn't actually connect, but prepares the socket
        s.connect(("8.8.8.8", 80))
        # Get the socket's own address, which is the local IP
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception as e:
        logger.error(f"Error getting IP address: {e}")
        # Fallback to get all local interfaces
        try:
            hostname = socket.gethostname()
            ip_list = socket.gethostbyname_ex(hostname)[2]
            # Filter out localhost (127.0.0.1)
            local_ips = [ip for ip in ip_list if not ip.startswith("127.")]
            # Return first non-localhost IP
            if local_ips:
                return local_ips[0]
        except:
            pass
        # Last resort
        return '127.0.0.1'


def generate_qr_code_terminal(url):
    """Generate and display a QR code in the terminal."""
    try:
        # Generate QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(url)
        qr.make(fit=True)

        # Create ASCII representation for terminal
        module_count = len(qr.modules)

        # Print header
        print("\n" + "=" * 60)
        print(f"  Game server running at: {url}")
        print(f"  Scan the QR code with your phone to join:")
        print("=" * 60 + "\n")

        # For better visibility in terminal, print two spaces for each module
        for row in range(module_count):
            line = ""
            for col in range(module_count):
                if qr.modules[row][col]:
                    line += "██"  # Black square
                else:
                    line += "  "  # White space
            print(line)

        print("\n" + "=" * 60)
        print(f"  Share this URL with players on the same network: {url}")
        print("=" * 60 + "\n")
    except Exception as e:
        logger.error(f"Error generating terminal QR code: {e}")


def generate_qr_code_html(url, filename="qr_code.html"):
    """Generate an HTML file with the QR code and open it in a browser."""
    try:
        # Generate QR code image
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4,
        )
        qr.add_data(url)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        # Save the image to a file
        img_path = os.path.join(os.path.dirname(
            os.path.abspath(__file__)), "qr_code.png")
        img.save(img_path)

        # Create HTML file
        html_path = os.path.join(os.path.dirname(
            os.path.abspath(__file__)), filename)

        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Game QR Code</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            text-align: center;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 600px;
            margin: 0 auto;
            background-color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
        }}
        h1 {{
            color: #333;
        }}
        .qr-code {{
            margin: 20px 0;
        }}
        .url {{
            margin: 20px 0;
            padding: 10px;
            background-color: #f0f0f0;
            border-radius: 4px;
            font-family: monospace;
            word-break: break-all;
        }}
        .button {{
            display: inline-block;
            margin-top: 20px;
            padding: 10px 20px;
            background-color: #4CAF50;
            color: white;
            text-decoration: none;
            border-radius: 4px;
            font-weight: bold;
        }}
        .button:hover {{
            background-color: #45a049;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Game Server QR Code</h1>
        <p>Scan this QR code with your phone camera to join the game:</p>
        <div class="qr-code">
            <img src="qr_code.png" alt="QR Code" style="max-width: 100%;">
        </div>
        <p>Or use this URL:</p>
        <div class="url">{url}</div>
        <a href="{url}" class="button">Open Game</a>
    </div>
</body>
</html>
"""

        with open(html_path, "w") as f:
            f.write(html_content)

        # Get the file URL
        file_url = f"file://{os.path.abspath(html_path)}"
        print(f"QR code HTML file generated at: {file_url}")

        return file_url, html_path
    except Exception as e:
        logger.error(f"Error generating HTML QR code: {e}")
        return None, None


def setup_qr_code(port=8000, auto_open_browser=True):
    """Set up QR code for the server URL and display it."""
    host = get_local_ip()
    server_url = f"http://{host}:{port}"

    # Display QR code in terminal
    generate_qr_code_terminal(server_url)

    # Generate HTML QR code
    html_url, html_path = generate_qr_code_html(server_url)

    # Open the QR code in browser if requested
    if auto_open_browser and html_url:
        try:
            print(f"Opening QR code in browser: {html_url}")
            webbrowser.open(html_url)
        except Exception as e:
            logger.error(f"Error opening browser: {e}")
            print(f"Please open the QR code manually at: {html_path}")

    return server_url
