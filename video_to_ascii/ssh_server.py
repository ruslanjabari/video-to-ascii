"""
SSH Server module to stream ASCII video to SSH clients
"""

import os
import socket
import sys
import threading
import paramiko
import argparse
import time
import cv2
from . import video_engine as ve

# Generate a key pair for the SSH server
if not os.path.exists('ssh_host_key'):
    key = paramiko.RSAKey.generate(2048)
    key.write_private_key_file('ssh_host_key')
else:
    key = paramiko.RSAKey(filename='ssh_host_key')

class SSHServerInterface(paramiko.ServerInterface):
    """SSH Server Interface to handle authentication and connections"""
    
    def __init__(self):
        self.event = threading.Event()
        self.username = None
        self.terminal_width = 80
        self.terminal_height = 24
        self.term_type = 'xterm'  # Default terminal type
        
    def check_channel_request(self, kind, chanid):
        if kind == 'session':
            return paramiko.OPEN_SUCCEEDED
        return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED
        
    def check_auth_password(self, username, password):
        # For now, accept any username/password
        # In a production environment, implement proper authentication
        self.username = username
        return paramiko.AUTH_SUCCESSFUL
        
    def check_auth_publickey(self, username, key):
        # For simplicity, accept any key
        self.username = username
        return paramiko.AUTH_SUCCESSFUL
        
    def get_allowed_auths(self, username):
        return 'password,publickey'
        
    def check_channel_shell_request(self, channel):
        self.event.set()
        return True
        
    def check_channel_pty_request(self, channel, term, width, height, pixelwidth, pixelheight, modes):
        """
        Handle PTY request with improved terminal dimension detection
        """
        self.term_type = term.decode('utf-8') if isinstance(term, bytes) else term
        
        # Store accurate terminal dimensions for rendering
        self.terminal_width = width if width > 0 else 80
        self.terminal_height = height if height > 0 else 24
        
        print(f"Client connected with terminal: {self.term_type}, dimensions: {self.terminal_width}x{self.terminal_height}")
        return True


class SSHStreamStrategy:
    """Strategy for streaming ASCII video to SSH clients"""
    
    def __init__(self, channel, server, video_path, strategy=None):
        self.channel = channel
        self.server = server  # Store server to access terminal dimensions
        self.video_path = video_path
        self.strategy = strategy
        self.engine = None
        
    def setup_engine(self):
        """Set up the video engine with the appropriate strategy"""
        self.engine = ve.VideoEngine()
        self.engine.load_video_from_file(self.video_path)
        if self.strategy:
            self.engine.set_strategy(self.strategy)
            print(f"Using strategy: {self.strategy}")
    
    def safe_send(self, data):
        """Send data safely in smaller chunks to prevent socket errors"""
        try:
            # Convert to bytes if it's a string
            if isinstance(data, str):
                data = data.encode('utf-8')
            
            # Send in smaller chunks (4KB)
            chunk_size = 4096
            for i in range(0, len(data), chunk_size):
                chunk = data[i:i+chunk_size]
                self.channel.send(chunk)
                time.sleep(0.001)  # Small delay between chunks
            return True
        except Exception as e:
            print(f"Send error: {str(e)}")
            return False
        
    def stream_to_client(self):
        """Stream video to SSH client"""
        try:
            # Let client know we're preparing the video
            self.safe_send("Preparing video for streaming...\r\n")
            time.sleep(0.5)
            
            # Use minimalist rendering to avoid connection issues
            cap = cv2.VideoCapture(self.video_path)
            if not cap.isOpened():
                self.safe_send("Error: Could not open video file.\r\n")
                return
            
            # Get video properties
            fps = cap.get(cv2.CAP_PROP_FPS) or 30
            time_delta = 1./fps
            
            # Very simple character set that works in all terminals
            ascii_chars = ' .:;+=xX$&@'
            
            # Clear screen
            self.safe_send("\033[2J\033[H")
            self.safe_send("Starting playback...\r\n\n")
            time.sleep(0.5)
            
            # Main playback loop
            frame_count = 0
            while cap.isOpened():
                t0 = time.time()
                ret, frame = cap.read()
                if not ret or frame is None:
                    break
                
                # Get safe terminal dimensions
                cols = max(30, min(self.server.terminal_width - 5, 80))
                rows = max(15, min(self.server.terminal_height - 5, 35))
                
                # For color version, use the strategy name to determine approach
                if self.strategy and any(s in self.strategy for s in ['color', 'adaptive', 'cinematic']):
                    # Try minimal color rendering - just 8 basic ANSI colors
                    # Convert frame to HSV for better color mapping
                    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
                    h, s, v = cv2.split(hsv)
                    
                    # Resize with correct aspect ratio
                    height, width = frame.shape[:2]
                    aspect_ratio = 0.4  # Terminal character aspect ratio
                    new_width = int(cols * aspect_ratio)
                    
                    # Resize all channels
                    h_resized = cv2.resize(h, (new_width, rows))
                    s_resized = cv2.resize(s, (new_width, rows))
                    v_resized = cv2.resize(v, (new_width, rows))
                    
                    # Generate ASCII output with color
                    lines = []
                    for y in range(rows):
                        line = ""
                        for x in range(new_width):
                            # Get pixel values
                            hue = h_resized[y, x]
                            sat = s_resized[y, x]
                            val = v_resized[y, x]
                            
                            # Map brightness to ASCII char
                            char_index = min(int(val / 255 * (len(ascii_chars) - 1)), len(ascii_chars) - 1)
                            char = ascii_chars[char_index]
                            
                            # Simple ANSI color mapping - 8 colors
                            color_code = 37  # Default white
                            
                            # Very simple color mapping
                            if sat > 50:  # Only color saturated pixels
                                if hue < 30 or hue > 150:  # Red
                                    color_code = 31
                                elif hue < 90:  # Green
                                    color_code = 32
                                elif hue < 150:  # Blue
                                    color_code = 34
                                elif hue < 180:  # Cyan
                                    color_code = 36
                                elif hue < 270:  # Magenta
                                    color_code = 35
                                else:  # Yellow
                                    color_code = 33
                                    
                            # Brightness - use bold for brighter pixels
                            bright = 1 if val > 128 else 0
                            
                            # Format with ANSI color
                            colored_char = f"\033[{bright};{color_code}m{char*2}\033[0m"
                            line += colored_char
                        
                        lines.append(line)
                    
                    # Join with proper newlines
                    output = "\r\n".join(lines)
                else:
                    # Use grayscale for non-color strategies
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    
                    # Resize with correct aspect ratio
                    height, width = gray.shape
                    aspect_ratio = 0.4  # Terminal character aspect ratio
                    new_width = int(cols * aspect_ratio)
                    gray_resized = cv2.resize(gray, (new_width, rows))
                    
                    # Generate ASCII output
                    lines = []
                    for y in range(rows):
                        line = ""
                        for x in range(new_width):
                            # Get pixel intensity and map to ASCII char
                            intensity = gray_resized[y, x]
                            char_index = min(int(intensity / 255 * (len(ascii_chars) - 1)), len(ascii_chars) - 1)
                            # Use character twice for better aspect ratio
                            line += ascii_chars[char_index] * 2
                        lines.append(line)
                    
                    # Format output with proper line endings for SSH
                    output = "\r\n".join(lines)
                
                # Debug info (first frame only)
                if frame_count == 0:
                    debug_info = f"Frame size: {width}x{height}, Terminal: {cols}x{rows}, Strategy: {self.strategy}\r\n"
                    self.safe_send(debug_info)
                    time.sleep(1)
                
                # Position cursor at top
                self.safe_send("\033[H")
                
                # Send frame
                success = self.safe_send(output)
                if not success:
                    print("Failed to send frame, connection may be closed")
                    break
                
                # Maintain framerate
                frame_count += 1
                elapsed = time.time() - t0
                sleep_time = max(0, time_delta - elapsed)
                time.sleep(sleep_time)
            
            # Clean up
            cap.release()
            self.safe_send("\r\n\r\nPlayback complete\r\n")
            
        except Exception as e:
            error_msg = f"Error streaming video: {str(e)}\r\n"
            print(error_msg)
            import traceback
            traceback.print_exc()
            try:
                self.safe_send(error_msg)
            except:
                pass
        finally:
            try:
                self.channel.close()
            except:
                pass


def handle_client(client, addr, video_path, strategy=None):
    """Handle an individual SSH client connection"""
    try:
        transport = paramiko.Transport(client)
        transport.set_keepalive(10)  # Enable keepalive to prevent timeout
        transport.add_server_key(key)
        
        server = SSHServerInterface()
        transport.start_server(server=server)
        
        # Wait for authentication
        channel = transport.accept(20)
        if channel is None:
            print(f"No channel from {addr}")
            return
        
        # Wait for shell request
        server.event.wait(10)
        if not server.event.is_set():
            print(f"No shell request from {addr}")
            return
        
        # Send welcome message
        channel.send("Welcome to Video-to-ASCII SSH Server!\r\n")
        channel.send(f"Streaming video: {os.path.basename(video_path)}\r\n")
        channel.send(f"Using strategy: {strategy or 'default'}\r\n")
        channel.send("Press Ctrl+C to exit\r\n\n")
        
        # Create stream and play video
        streamer = SSHStreamStrategy(channel, server, video_path, strategy)
        streamer.setup_engine()
        streamer.stream_to_client()
        
    except Exception as e:
        print(f"Error handling client {addr}: {str(e)}")
    finally:
        try:
            transport.close()
        except:
            pass


def run_server(video_path, host='0.0.0.0', port=2222, strategy=None):
    """Run the SSH server"""
    # Verify the video file exists
    if not os.path.exists(video_path):
        print(f"Error: Video file '{video_path}' not found")
        return
    
    # Create socket
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((host, port))
        sock.listen(100)
        print(f"SSH Video-to-ASCII server running on {host}:{port}")
        print(f"Streaming video: {video_path}")
        print(f"Using strategy: {strategy or 'default'}")
        print("Press Ctrl+C to stop the server")
        
        # Accept connections
        while True:
            client, addr = sock.accept()
            print(f"Connection from {addr[0]}:{addr[1]}")
            
            # Handle each client in a separate thread
            t = threading.Thread(target=handle_client, args=(client, addr, video_path, strategy))
            t.daemon = True
            t.start()
            
    except KeyboardInterrupt:
        print("Server shutting down...")
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        try:
            sock.close()
        except:
            pass


def main():
    """CLI entry point for the SSH server"""
    parser = argparse.ArgumentParser(description="Video-to-ASCII SSH Server")
    parser.add_argument('-f', '--file', type=str, dest='file', 
                        help='input video file', required=True)
    parser.add_argument('--host', type=str, default='0.0.0.0',
                        help='host to bind server to')
    parser.add_argument('--port', type=int, default=2222,
                        help='port to run server on')
    parser.add_argument('--strategy', default='ascii-color', type=str, 
                        dest='strategy', 
                        choices=["ascii-color", "just-ascii", "filled-ascii", 
                                "adaptive", "cinematic"], 
                        help='choose a strategy to render the output')
    
    args = parser.parse_args()
    
    run_server(args.file, args.host, args.port, args.strategy)


if __name__ == '__main__':
    main() 