"""TCP Socket Server executing dynamic post-quantum cryptographic handshakes."""

import socket
import sys
import threading
from typing import Optional
from aqpqc.catalog import ALGORITHM_CATALOG, get_algorithm
from demo.protocol import DynamicPQCHandshake

class PQCHandshakeServer:
    """Server that negotiates dynamic PQC KEM primitives and establishes encrypted sessions."""

    def __init__(self, host: str = "127.0.0.1", port: int = 9999):
        self.host = host
        self.port = port
        self._running = False
        self._server_sock: Optional[socket.socket] = None

    def handle_client(self, conn: socket.socket, addr):
        try:
            # 1. Receive Client Hello
            hello = DynamicPQCHandshake.recv_frame(conn)
            if hello.get("type") != "CLIENT_HELLO":
                DynamicPQCHandshake.send_frame(conn, {"type": "ERROR", "message": "Expected CLIENT_HELLO"})
                return

            algo_name = hello.get("algorithm")
            pk_bytes = bytes.fromhex(hello.get("public_key_hex", ""))

            algo = get_algorithm(algo_name)
            if algo.op_type != "kem":
                DynamicPQCHandshake.send_frame(conn, {"type": "ERROR", "message": "Must be KEM algorithm"})
                return

            # 2. Encapsulate shared secret
            ciphertext, shared_secret = DynamicPQCHandshake.encapsulate(algo_name, pk_bytes)
            session_key = DynamicPQCHandshake.derive_session_key(shared_secret)

            # 3. Send Server Hello with Ciphertext
            DynamicPQCHandshake.send_frame(conn, {
                "type": "SERVER_HELLO",
                "status": "OK",
                "algorithm": algo_name,
                "ciphertext_hex": ciphertext.hex(),
            })

            # 4. Handle secure application data exchange
            msg = DynamicPQCHandshake.recv_frame(conn)
            if msg.get("type") == "SECURE_DATA":
                payload = msg.get("payload", "")
                tag = msg.get("auth_tag", "")
                expected_tag = DynamicPQCHandshake.compute_auth_tag(session_key, payload)

                if tag == expected_tag:
                    ack_payload = "PQC_HANDSHAKE_ACK"
                    ack_tag = DynamicPQCHandshake.compute_auth_tag(session_key, ack_payload)
                    DynamicPQCHandshake.send_frame(conn, {
                        "type": "SECURE_DATA",
                        "payload": ack_payload,
                        "auth_tag": ack_tag,
                    })

        except Exception as e:
            try:
                DynamicPQCHandshake.send_frame(conn, {"type": "ERROR", "message": str(e)})
            except Exception:
                pass
        finally:
            conn.close()

    def serve_forever(self):
        self._server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._server_sock.bind((self.host, self.port))
        self._server_sock.listen(5)
        self._running = True

        while self._running:
            try:
                conn, addr = self._server_sock.accept()
                t = threading.Thread(target=self.handle_client, args=(conn, addr), daemon=True)
                t.start()
            except OSError:
                break

    def shutdown(self):
        self._running = False
        if self._server_sock:
            self._server_sock.close()


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 9999
    server = PQCHandshakeServer(port=port)
    print(f"PQC Handshake Server listening on 127.0.0.1:{port}...")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server.")
        server.shutdown()


if __name__ == "__main__":
    main()
