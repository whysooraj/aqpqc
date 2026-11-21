"""NIST Post-Quantum Cryptography algorithm catalog and specifications."""

from dataclasses import dataclass
from typing import Dict, List, Literal, Optional

OpType = Literal["kem", "sign"]

@dataclass(frozen=True)
class PQCAlgorithm:
    name: str
    standard_name: str
    op_type: OpType
    security_level: int  # NIST Level: 1, 2, 3, 5
    public_key_bytes: int
    private_key_bytes: int
    ciphertext_bytes: int = 0
    signature_bytes: int = 0
    estimated_cycles_keygen: int = 0
    estimated_cycles_operation: int = 0  # encap/sign
    estimated_cycles_verify: int = 0     # decap/verify
    memory_footprint_kb: float = 0.0
    description: str = ""

# Authoritative NIST PQC specification standards (FIPS 203, 204, 205 + Falcon)
ALGORITHM_CATALOG: Dict[str, PQCAlgorithm] = {
    # Key Encapsulation Mechanisms (FIPS 203 / ML-KEM)
    "ML-KEM-512": PQCAlgorithm(
        name="ML-KEM-512",
        standard_name="FIPS 203",
        op_type="kem",
        security_level=1,
        public_key_bytes=800,
        private_key_bytes=1632,
        ciphertext_bytes=768,
        estimated_cycles_keygen=48000,
        estimated_cycles_operation=62000,
        estimated_cycles_verify=55000,
        memory_footprint_kb=16.0,
        description="Lattice-based KEM matching AES-128 equivalent security with lowest bandwidth overhead."
    ),
    "ML-KEM-768": PQCAlgorithm(
        name="ML-KEM-768",
        standard_name="FIPS 203",
        op_type="kem",
        security_level=3,
        public_key_bytes=1184,
        private_key_bytes=2400,
        ciphertext_bytes=1088,
        estimated_cycles_keygen=82000,
        estimated_cycles_operation=98000,
        estimated_cycles_verify=89000,
        memory_footprint_kb=24.0,
        description="Recommended default general-purpose post-quantum KEM matching AES-192 security."
    ),
    "ML-KEM-1024": PQCAlgorithm(
        name="ML-KEM-1024",
        standard_name="FIPS 203",
        op_type="kem",
        security_level=5,
        public_key_bytes=1568,
        private_key_bytes=3168,
        ciphertext_bytes=1568,
        estimated_cycles_keygen=124000,
        estimated_cycles_operation=145000,
        estimated_cycles_verify=135000,
        memory_footprint_kb=32.0,
        description="Highest security level KEM matching AES-256 security for high-assurance data."
    ),
    # Digital Signatures (FIPS 204 / ML-DSA)
    "ML-DSA-44": PQCAlgorithm(
        name="ML-DSA-44",
        standard_name="FIPS 204",
        op_type="sign",
        security_level=2,
        public_key_bytes=1312,
        private_key_bytes=2560,
        signature_bytes=2420,
        estimated_cycles_keygen=120000,
        estimated_cycles_operation=410000,
        estimated_cycles_verify=180000,
        memory_footprint_kb=32.0,
        description="Primary lattice signature standard at NIST Security Level 2."
    ),
    "ML-DSA-65": PQCAlgorithm(
        name="ML-DSA-65",
        standard_name="FIPS 204",
        op_type="sign",
        security_level=3,
        public_key_bytes=1952,
        private_key_bytes=4032,
        signature_bytes=3309,
        estimated_cycles_keygen=230000,
        estimated_cycles_operation=750000,
        estimated_cycles_verify=310000,
        memory_footprint_kb=48.0,
        description="General enterprise digital signature scheme matching NIST Security Level 3."
    ),
    "ML-DSA-87": PQCAlgorithm(
        name="ML-DSA-87",
        standard_name="FIPS 204",
        op_type="sign",
        security_level=5,
        public_key_bytes=2592,
        private_key_bytes=4896,
        signature_bytes=4627,
        estimated_cycles_keygen=350000,
        estimated_cycles_operation=1120000,
        estimated_cycles_verify=490000,
        memory_footprint_kb=64.0,
        description="Maximum assurance post-quantum digital signature matching NIST Security Level 5."
    ),
    # Falcon Digital Signatures (Compact lattice signatures)
    "Falcon-512": PQCAlgorithm(
        name="Falcon-512",
        standard_name="NIST Round 3",
        op_type="sign",
        security_level=1,
        public_key_bytes=897,
        private_key_bytes=1281,
        signature_bytes=666,
        estimated_cycles_keygen=19000000,
        estimated_cycles_operation=380000,
        estimated_cycles_verify=82000,
        memory_footprint_kb=72.0,
        description="Compact lattice signature with tiny signature size (666B), requiring floating-point support."
    ),
    "Falcon-1024": PQCAlgorithm(
        name="Falcon-1024",
        standard_name="NIST Round 3",
        op_type="sign",
        security_level=5,
        public_key_bytes=1793,
        private_key_bytes=2305,
        signature_bytes=1280,
        estimated_cycles_keygen=41000000,
        estimated_cycles_operation=780000,
        estimated_cycles_verify=165000,
        memory_footprint_kb=128.0,
        description="High-security compact lattice signature with 1280-byte signature size."
    ),
    # Stateless Hash-Based Signatures (FIPS 205 / SLH-DSA)
    "SLH-DSA-SHAKE-128s": PQCAlgorithm(
        name="SLH-DSA-SHAKE-128s",
        standard_name="FIPS 205",
        op_type="sign",
        security_level=1,
        public_key_bytes=32,
        private_key_bytes=64,
        signature_bytes=7856,
        estimated_cycles_keygen=2200000,
        estimated_cycles_operation=84000000,
        estimated_cycles_verify=3200000,
        memory_footprint_kb=16.0,
        description="Stateless hash-based signature with conservative security proofs and tiny 32-byte public key."
    ),
}

def get_algorithm(name: str) -> PQCAlgorithm:
    """Retrieve algorithm by standardized name."""
    if name not in ALGORITHM_CATALOG:
        raise KeyError(f"Unknown algorithm '{name}'. Available: {list(ALGORITHM_CATALOG.keys())}")
    return ALGORITHM_CATALOG[name]

def list_algorithms(op_type: Optional[OpType] = None) -> List[PQCAlgorithm]:
    """List available algorithms, optionally filtered by operation type (kem/sign)."""
    if op_type is None:
        return list(ALGORITHM_CATALOG.values())
    return [algo for algo in ALGORITHM_CATALOG.values() if algo.op_type == op_type]
