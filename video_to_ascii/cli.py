"""This module contains a CLI interface"""

from . import player
from . import ssh_server

def main():
    import argparse

    CLI_DESC = "It is a simple python package to play videos in the terminal using colored characters as pixels or other useful outputs"
    EPILOG = ("\033[1;37mThanks for trying video-to-ascii!\033[0m")

    PARSER = argparse.ArgumentParser(prog='video-to-ascii', description=CLI_DESC, epilog=EPILOG)
    PARSER.add_argument('-f', '--file', type=str, dest='file', help='input video file', action='store', required=True)
    PARSER.add_argument('--strategy', default='ascii-color', type=str, dest='strategy', 
        choices=["ascii-color", "just-ascii", "filled-ascii", "adaptive", "cinematic"], 
        help='choose a strategy to render the output', action='store')
    PARSER.add_argument('-o', '--output', type=str, dest='output', help='output file to export', action='store')
    PARSER.add_argument('-a','--with-audio', dest='with_audio', help='play audio track', action='store_true')
    PARSER.add_argument('--server', dest='server_mode', help='run as SSH server', action='store_true')
    PARSER.add_argument('--port', type=int, dest='port', default=2222, help='SSH server port (with --server)')
    PARSER.add_argument('--host', type=str, dest='host', default='0.0.0.0', help='SSH server host (with --server)')

    ARGS = PARSER.parse_args()

    try:
        if ARGS.server_mode:
            # Run in SSH server mode
            ssh_server.run_server(ARGS.file, ARGS.host, ARGS.port, ARGS.strategy)
        else:
            # Run in normal mode
            player.play(ARGS.file, strategy=ARGS.strategy, output=ARGS.output, play_audio=ARGS.with_audio)
    except (KeyboardInterrupt):
        pass

if __name__ == '__main__':
    main()
