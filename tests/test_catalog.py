# tests/test_catalog.py
import pytest
from aqpqc.catalog import ALGORITHM_CATALOG, PQCAlgorithm, get_algorithm, list_algorithms

def test_catalog_contains_nist_standards():
    kem_algos = list_algorithms(op_type="kem")
    sign_algos = list_algorithms(op_type="sign")
    assert len(kem_algos) >= 3
    assert len(sign_algos) >= 4

    kyber512 = get_algorithm("ML-KEM-512")
    assert isinstance(kyber512, PQCAlgorithm)
    assert kyber512.public_key_bytes == 800
    assert kyber512.ciphertext_bytes == 768
    assert kyber512.security_level == 1
    assert kyber512.op_type == "kem"

    dsa44 = get_algorithm("ML-DSA-44")
    assert isinstance(dsa44, PQCAlgorithm)
    assert dsa44.public_key_bytes == 1312
    assert dsa44.signature_bytes == 2420
    assert dsa44.security_level == 2
    assert dsa44.op_type == "sign"

def test_get_nonexistent_algorithm():
    with pytest.raises(KeyError):
        get_algorithm("NON_EXISTENT_CIPHER")
