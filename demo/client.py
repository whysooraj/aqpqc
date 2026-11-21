"""TCP Socket Client using AQPQC Selector for context-adaptive PQC handshakes."""

import socket
import sys
from typing import Any, Dict, Optional

from aqpqc.selector import AQPQCSelector
from aqpqc.telemetry import TelemetryCollector, TelemetrySnapshot
from demo.protocol import DynamicPQCHandshake

class PQCHandshakeClient:
    """Client that inspects network telemetry, selects optimal PQC KEM, and performs handshake."""

    def __init__(self, host: str = "127.0.0.1", port: int = 9999):
        self.host = host
        self.port = port
        self.selector = AQPQCSelector()

    def run_handshake(
        self,
        context: Optional[TelemetrySnapshot] = None,
        min_security: int = 1,
    ) -> Dict[str, Any]:
        """Execute complete adaptive PQC handshake workflow."""
        # 1. Probe context & query AQPQC Selector
        if context is None:
            collector = TelemetryCollector(default_host=self.host, default_port=self.port)
            context = collector.collect()

        rec = self.selector.recommend(context, op_type="kem", min_security=min_security)
        algo_name = rec.algorithm

        # 2. Generate Keypair for the selected PQC algorithm
        pk, sk = DynamicPQCHandshake.generate_keypair(algo_name)

        # 3. Connect to server
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3.0)
        sock.connect((self.host, self.port))

        try:
            # 4. Send Client Hello
            DynamicPQCHandshake.send_frame(sock, {
                "type": "CLIENT_HELLO",
                "algorithm": algo_name,
                "public_key_hex": pk.hex(),
            })

            # 5. Receive Server Hello with Ciphertext
            res = DynamicPQCHandshake.recv_frame(sock)
            if res.get("status") != "OK":
                raise ConnectionError(f"Handshake rejected: {res.get('message')}")

            ciphertext = bytes.fromhex(res["ciphertext_hex"])

            # 6. Decapsulate shared secret & derive session key
            shared_secret = DynamicPQCHandshake.decapsulate(algo_name, ciphertext, sk)
            session_key = DynamicPQCHandshake.derive_session_key(shared_secret)

            # 7. Send authenticated session payload
            ping_msg = "PQC_PING"
            tag = DynamicPQCHandshake.compute_auth_tag(session_key, ping_msg)
            DynamicPQCHandshake.send_frame(sock, {
                "type": "SECURE_DATA",
                "payload": ping_msg,
                "auth_tag": tag,
            })

            # 8. Receive authenticated ACK
            ack_msg = DynamicPQCHandshake.recv_frame(sock)
            ack_payload = ack_msg.get("payload", "")
            ack_tag = ack_msg.get("auth_tag", "")
            expected_ack_tag = DynamicPQCHandshake.compute_auth_tag(session_key, ack_payload)

            if ack_tag != expected_ack_tag:
                raise ValueError("Session key HMAC authentication failed on server ACK")

            return {
                "success": True,
                "algorithm": algo_name,
                "confidence": rec.confidence,
                "explanation": rec.explanation,
                "session_key_hex": session_key.hex(),
                "echo_response": ack_payload,
                "telemetry": context.to_dict(),
            }

        finally:
            sock.close()


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 9999
    client = PQCHandshakeClient(port=port)
    print(f"Connecting to PQC server on 127.0.0.1:{port}...")
    result = client.run_handshake()
    print("\nHandshake Successful!")
    print(f"  Negotiated Algorithm: {result['algorithm']}")
    print(f"  Confidence:           {result['confidence']*100:.1f}%")
    print(f"  Session Key:          {result['session_key_hex']}")
    print(f"  Server Response:      {result['echo_response']}")
    print(f"  Rationale:            {result['explanation']}")


if __name__ == "__main__":
    main()
