import argparse
import asyncore
from   serial import Serial
import signal
import socket
import sys

class Server(asyncore.dispatcher):
    def __init__(self, tcp_address='0.0.0.0', tcp_port=0, recv_buffer_size=1024, *serial_args, **serial_kwargs):
        asyncore.dispatcher.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.bind((tcp_address, tcp_port))
        self.listen(1)
        self.recv_buffer_size = recv_buffer_size
        self.serial_args      = serial_args
        self.serial_kwargs    = serial_kwargs

    def _tcp_port(self):
        return self.socket.getsockname()[1]
    tcp_port = property(_tcp_port)
    def handle_accept(self):
        sock, addr = self.accept()
        Handler(sock, self.recv_buffer_size, Serial(*self.serial_args, **self.serial_kwargs))

class Handler(asyncore.dispatcher_with_send):
    def __init__(self, sock, recv_buffer_size, serial):
        asyncore.dispatcher_with_send.__init__(self, sock)
        self.recv_buffer_size = recv_buffer_size
        self.serial = serial
    def handle_read(self):
        self.serial.write(self.recv(self.recv_buffer_size))
        self.send(self.serial.readall())

def main():
    parser = argparse.ArgumentParser(description='TCP server for controlling multiple RFFEs via SCPI')
    parser.add_argument('--tcp-address',      '-a', type=str,   default='0.0.0.0')
    parser.add_argument('--tcp-port',         '-p', type=int,   default=0)
    parser.add_argument('--recv-buffer-size', '-r', type=int,   default=1024)
    parser.add_argument('--baud-rate',        '-b', type=int,   default=9600)
    parser.add_argument('--serial-timeout',   '-t', type=float, default=0.1)
    parser.add_argument('--disable-rts',      '-s',             action='store_true')
    parser.add_argument('--disable-dtr',      '-d',             action='store_true')
    parser.add_argument('serial_port')
    args = parser.parse_args()

    server = Server(args.tcp_address, args.tcp_port, args.recv_buffer_size, port=args.serial_port, timeout=args.serial_timeout, baudrate=args.baud_rate)
    server.rts = not args.disable_rts
    server.dtr = not args.disable_dtr
    def sys_exit(*args):
        sys.exit(0)
    signal.signal(signal.SIGTERM, sys_exit)

    try:
        if not args.tcp_port:
            print('tcp-port {0}'.format(args.tcp_port), flush=True)
        asyncore.loop()
    except KeyboardInterrupt:
        pass
    finally:
        asyncore.close_all()
        sys.exit(0)

if __name__ == '__main__':
    main()
