"""Context-aware post-quantum cryptographic algorithm selector using XGBoost and Pareto ranking."""

from dataclasses import asdict, dataclass
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import numpy as np

try:
    from xgboost import XGBClassifier
    _USE_XGBOOST = True
except ImportError:
    from sklearn.ensemble import GradientBoostingClassifier
    _USE_XGBOOST = False

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

from aqpqc.catalog import ALGORITHM_CATALOG, get_algorithm, list_algorithms
from aqpqc.dataset import FEATURE_NAMES, calculate_pareto_utility, generate_synthetic_dataset
from aqpqc.explain import generate_decision_explanation
from aqpqc.telemetry import TelemetrySnapshot

@dataclass
class SelectionResult:
    algorithm: str
    standard_name: str
    op_type: str
    security_level: int
    confidence: float
    top_candidates: List[Dict[str, Any]]
    explanation: str
    telemetry: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class AQPQCSelector:
    """Adaptive context-aware selector combining XGBoost probability scoring with Pareto utility."""

    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path
        self.model: Any = None
        self.label_encoder = LabelEncoder()
        self.class_names: List[str] = sorted(list(ALGORITHM_CATALOG.keys()))
        self.feature_names = FEATURE_NAMES
        self.feature_importances_: Dict[str, float] = {}
        self.is_trained: bool = False

    def train(self, n_samples: int = 1000, random_state: int = 42) -> float:
        """Train context classifier using synthetic Pareto-labeled dataset."""
        X, y_raw, self.class_names, self.feature_names = generate_synthetic_dataset(
            n_samples=n_samples, random_state=random_state
        )

        # Encode classes into contiguous integers 0..k-1
        y_encoded = self.label_encoder.fit_transform(y_raw)

        X_train, X_val, y_train, y_val = train_test_split(
            X, y_encoded, test_size=0.2, random_state=random_state, stratify=y_encoded
        )

        if _USE_XGBOOST:
            self.model = XGBClassifier(
                n_estimators=80,
                max_depth=5,
                learning_rate=0.1,
                eval_metric="mlogloss",
                random_state=random_state,
                n_jobs=-1,
            )
        else:
            self.model = GradientBoostingClassifier(
                n_estimators=60,
                max_depth=4,
                random_state=random_state,
            )

        self.model.fit(X_train, y_train)
        accuracy = float(self.model.score(X_val, y_val))
        self.is_trained = True

        # Extract feature importances
        if hasattr(self.model, "feature_importances_"):
            self.feature_importances_ = {
                name: float(imp) for name, imp in zip(self.feature_names, self.model.feature_importances_)
            }

        return accuracy

    def recommend(
        self,
        context: TelemetrySnapshot,
        op_type: str = "kem",
        min_security: int = 1,
    ) -> SelectionResult:
        """Recommend optimal post-quantum algorithm matching operational context and security bounds."""
        if not self.is_trained:
            self.train(n_samples=500)

        is_sign = 1.0 if op_type == "sign" else 0.0
        feature_vec = np.array(
            [[
                context.cpu_usage_pct,
                context.mem_available_mb,
                context.network_rtt_ms,
                context.network_bandwidth_mbps,
                context.packet_loss_pct,
                float(context.mtu_bytes),
                float(min_security),
                is_sign,
            ]],
            dtype=np.float32,
        )

        # Predict probability across model classes
        probs = self.model.predict_proba(feature_vec)[0]
        model_classes = self.label_encoder.classes_  # Array of original class indices

        # Build map of algo_name -> model probability
        name_to_prob: Dict[str, float] = {}
        for encoded_idx, raw_idx in enumerate(model_classes):
            name = self.class_names[raw_idx]
            name_to_prob[name] = float(probs[encoded_idx])

        # Filter candidate algorithms by operation type and minimum security level
        candidates = list_algorithms(op_type=op_type)  # type: ignore
        valid_candidates = [c for c in candidates if c.security_level >= min_security]
        if not valid_candidates:
            valid_candidates = candidates

        candidate_scores: List[Tuple[str, float, float]] = []
        for cand in valid_candidates:
            p_score = name_to_prob.get(cand.name, 0.0)

            # Compute Pareto utility to guarantee physical constraint satisfaction
            pareto_score = calculate_pareto_utility(
                algo_name=cand.name,
                cpu_usage_pct=context.cpu_usage_pct,
                mem_available_mb=context.mem_available_mb,
                network_rtt_ms=context.network_rtt_ms,
                network_bandwidth_mbps=context.network_bandwidth_mbps,
                packet_loss_pct=context.packet_loss_pct,
                mtu_bytes=context.mtu_bytes,
                required_security=min_security,
            )

            # Composite ranking: ML probability + Pareto satisfaction
            combined = p_score * 0.6 + (max(pareto_score, -500.0) / 100.0) * 0.4
            candidate_scores.append((cand.name, combined, p_score))

        # Sort descending by score
        candidate_scores.sort(key=lambda x: x[1], reverse=True)
        best_name, best_score, raw_prob = candidate_scores[0]
        best_algo = get_algorithm(best_name)

        confidence = max(min(raw_prob if raw_prob > 0 else 0.95, 0.99), 0.50)

        # Build top candidate records
        top_list: List[Dict[str, Any]] = []
        for name, score, prob in candidate_scores[:3]:
            algo_info = get_algorithm(name)
            top_list.append({
                "algorithm": name,
                "security_level": algo_info.security_level,
                "score": round(score, 3),
                "model_probability": round(prob, 3),
                "public_key_bytes": algo_info.public_key_bytes,
                "payload_bytes": algo_info.ciphertext_bytes if op_type == "kem" else algo_info.signature_bytes,
            })

        explanation = generate_decision_explanation(
            algo_name=best_name,
            context=context,
            op_type=op_type,
            min_security=min_security,
            confidence=confidence,
            feature_importances=self.feature_importances_,
        )

        return SelectionResult(
            algorithm=best_algo.name,
            standard_name=best_algo.standard_name,
            op_type=best_algo.op_type,
            security_level=best_algo.security_level,
            confidence=round(confidence, 3),
            top_candidates=top_list,
            explanation=explanation,
            telemetry=context.to_dict(),
        )
