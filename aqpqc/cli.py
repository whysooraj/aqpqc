"""Command Line Interface for AQPQC Selector."""

import argparse
import json
import sys
from typing import List, Optional

from aqpqc.benchmark import BenchmarkEngine
from aqpqc.catalog import ALGORITHM_CATALOG, list_algorithms
from aqpqc.selector import AQPQCSelector
from aqpqc.telemetry import TelemetryCollector, TelemetrySnapshot

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="aqpqc",
        description="AQPQC Selector: Adaptive Quantum Intelligence Framework for Context-Aware Post-Quantum Cryptographic Algorithm Selection",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # 1. catalog command
    catalog_parser = subparsers.add_parser("catalog", help="List supported NIST PQC algorithms")
    catalog_parser.add_argument("--op", choices=["kem", "sign"], help="Filter by operation type (kem or sign)")
    catalog_parser.add_argument("--json", action="store_true", help="Output catalog as JSON")

    # 2. telemetry command
    telem_parser = subparsers.add_parser("telemetry", help="Sample current hardware and network context")
    telem_parser.add_argument("--no-network-probe", action="store_true", help="Skip remote network latency probing")
    telem_parser.add_argument("--json", action="store_true", help="Output telemetry as JSON")

    # 3. benchmark command
    bench_parser = subparsers.add_parser("benchmark", help="Run benchmarks on PQC algorithms")
    bench_parser.add_argument("--algo", help="Benchmark a single algorithm by name")
    bench_parser.add_argument("--op", choices=["kem", "sign"], help="Filter by operation type")
    bench_parser.add_argument("--iterations", type=int, default=5, help="Number of benchmark iterations")
    bench_parser.add_argument("--json", action="store_true", help="Output benchmark results as JSON")

    # 4. train command
    train_parser = subparsers.add_parser("train", help="Train context-aware XGBoost selector model")
    train_parser.add_argument("--samples", type=int, default=1000, help="Number of synthetic context scenarios")
    train_parser.add_argument("--json", action="store_true", help="Output training metrics as JSON")

    # 5. select command
    select_parser = subparsers.add_parser("select", help="Select optimal PQC algorithm for context")
    select_parser.add_argument("--op", choices=["kem", "sign"], default="kem", help="Target cryptographic operation")
    select_parser.add_argument("--security", type=int, choices=[1, 2, 3, 5], default=1, help="Minimum NIST security level")
    select_parser.add_argument("--cpu", type=float, help="Override CPU utilization percentage")
    select_parser.add_argument("--mem", type=float, help="Override available memory in MB")
    select_parser.add_argument("--rtt", type=float, help="Override network RTT in ms")
    select_parser.add_argument("--bw", type=float, help="Override bandwidth in Mbps")
    select_parser.add_argument("--loss", type=float, help="Override packet loss percentage")
    select_parser.add_argument("--mtu", type=int, help="Override network MTU in bytes")
    select_parser.add_argument("--no-network-probe", action="store_true", help="Skip active network probing")
    select_parser.add_argument("--json", action="store_true", help="Output recommendation as JSON")

    # 6. serve command
    serve_parser = subparsers.add_parser("serve", help="Start FastAPI REST microservice")
    serve_parser.add_argument("--host", default="0.0.0.0", help="Host interface to bind")
    serve_parser.add_argument("--port", type=int, default=8000, help="Port to listen on")

    return parser


def run_cli(args: argparse.Namespace) -> int:
    cmd = args.command

    if cmd == "catalog":
        algos = list_algorithms(op_type=args.op)
        if args.json:
            print(json.dumps([a.__dict__ for a in algos], indent=2))
        else:
            print(f"{'ALGORITHM':<20} {'STANDARD':<14} {'TYPE':<6} {'SEC':<5} {'PUBKEY(B)':<10} {'PAYLOAD(B)':<10}")
            print("-" * 72)
            for a in algos:
                payload = a.ciphertext_bytes if a.op_type == "kem" else a.signature_bytes
                print(f"{a.name:<20} {a.standard_name:<14} {a.op_type:<6} {a.security_level:<5} {a.public_key_bytes:<10} {payload:<10}")
        return 0

    if cmd == "telemetry":
        collector = TelemetryCollector()
        snapshot = collector.collect(probe_network=not args.no_network_probe)
        if args.json:
            print(json.dumps(snapshot.to_dict(), indent=2))
        else:
            print("=== Runtime Context Telemetry ===")
            print(f"  CPU Utilization:    {snapshot.cpu_usage_pct:.1f}%")
            print(f"  Available Memory:   {snapshot.mem_available_mb:.1f} MB")
            print(f"  Network RTT:        {snapshot.network_rtt_ms:.2f} ms")
            print(f"  Estimated Bandwidth:{snapshot.network_bandwidth_mbps:.1f} Mbps")
            print(f"  Packet Loss Rate:   {snapshot.packet_loss_pct:.1f}%")
            print(f"  Network MTU:        {snapshot.mtu_bytes} Bytes")
        return 0

    if cmd == "benchmark":
        engine = BenchmarkEngine()
        if args.algo:
            results = [engine.benchmark(args.algo, iterations=args.iterations)]
        else:
            results = engine.benchmark_all(op_type=args.op, iterations=args.iterations)

        if args.json:
            print(json.dumps([r.to_dict() for r in results], indent=2))
        else:
            print(f"Engine backend: {'liboqs (native C)' if engine.has_liboqs else 'calibrated NIST timing model'}")
            print(f"{'ALGORITHM':<20} {'TYPE':<6} {'OP TIME (us)':<14} {'KEYGEN (us)':<14} {'VERIFY (us)':<14} {'RAM (KB)':<10}")
            print("-" * 80)
            for r in results:
                print(f"{r.algorithm:<20} {r.op_type:<6} {r.op_time_us:<14.2f} {r.keygen_time_us:<14.2f} {r.verify_time_us:<14.2f} {r.memory_peak_kb:<10.1f}")
        return 0

    if cmd == "train":
        selector = AQPQCSelector()
        acc = selector.train(n_samples=args.samples)
        if args.json:
            print(json.dumps({
                "samples": args.samples,
                "validation_accuracy": round(acc, 4),
                "feature_importances": selector.feature_importances_,
            }, indent=2))
        else:
            print(f"Trained AQPQCSelector on {args.samples} synthetic contexts.")
            print(f"Validation Accuracy: {acc*100.0:.2f}%")
            print("\nFeature Importances:")
            for feat, imp in sorted(selector.feature_importances_.items(), key=lambda x: x[1], reverse=True):
                print(f"  {feat:<24} : {imp*100.0:.2f}%")
        return 0

    if cmd == "select":
        collector = TelemetryCollector()
        snapshot = collector.collect(probe_network=not args.no_network_probe)

        # Apply user overrides if specified
        if args.cpu is not None:
            snapshot.cpu_usage_pct = args.cpu
        if args.mem is not None:
            snapshot.mem_available_mb = args.mem
        if args.rtt is not None:
            snapshot.network_rtt_ms = args.rtt
        if args.bw is not None:
            snapshot.network_bandwidth_mbps = args.bw
        if args.loss is not None:
            snapshot.packet_loss_pct = args.loss
        if args.mtu is not None:
            snapshot.mtu_bytes = args.mtu

        selector = AQPQCSelector()
        result = selector.recommend(
            context=snapshot,
            op_type=args.op,
            min_security=args.security,
        )

        if args.json:
            print(json.dumps(result.to_dict(), indent=2))
        else:
            print("\n=== AQPQC Selection Recommendation ===")
            print(f"  Recommended Algorithm: {result.algorithm}")
            print(f"  Standard:              {result.standard_name}")
            print(f"  Operation:             {result.op_type.upper()}")
            print(f"  NIST Security Level:   Level {result.security_level}")
            print(f"  Confidence:            {result.confidence * 100.0:.1f}%\n")
            print("  Top Ranked Candidates:")
            for cand in result.top_candidates:
                print(f"    - {cand['algorithm']} (Level {cand['security_level']}): score={cand['score']}, pubkey={cand['public_key_bytes']}B, payload={cand['payload_bytes']}B")
            print(f"\n  Rationale:\n    {result.explanation}\n")
        return 0

    if cmd == "serve":
        try:
            import uvicorn
            from aqpqc.api import app
            print(f"Starting AQPQC REST Microservice on http://{args.host}:{args.port}")
            uvicorn.run(app, host=args.host, port=args.port)
            return 0
        except ImportError:
            print("Error: uvicorn and fastapi are required to run the service. Install with 'pip install .[api]'.", file=sys.stderr)
            return 1

    return 1


def main():
    parser = build_parser()
    args = parser.parse_args()
    sys.exit(run_cli(args))


if __name__ == "__main__":
    main()
