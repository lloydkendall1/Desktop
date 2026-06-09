"""
Loads one trained classifier bundle (model + scaler + label_encoder, saved by
your notebook's Step 12 joblib.dump) and turns a MediaPipe pose result into a
(label, confidence) verdict.

This is the runtime half of your validation notebook's live loop, but it no
longer reads the training CSV to recover the column order — it uses
features.feature_names(), which reproduces that order in code.
"""

import joblib
import pandas as pd

from services.config import MIN_PROB, NO_POSE_LABEL, UNCERTAIN_LABEL
from services.features import feature_names, result_to_feature_vector


class PostureClassifier:
    def __init__(self, model_path: str, min_prob: float = MIN_PROB):
        bundle = joblib.load(model_path)
        self.model = bundle["model"]
        self.scaler = bundle["scaler"]
        self.label_encoder = bundle["label_encoder"]
        self.min_prob = min_prob
        self.feature_order = feature_names()

    def predict(self, result) -> tuple[str, float]:
        """
        Returns (label, confidence).
        - No person in frame       -> (NO_POSE_LABEL, 1.0)
        - Below the prob threshold -> (UNCERTAIN_LABEL, confidence)
        - Otherwise                -> (predicted class name, confidence)
        """
        vector = result_to_feature_vector(result)
        if vector is None:
            return NO_POSE_LABEL, 1.0

        # Wrap the (1, 140) array in a DataFrame whose column names match the
        # ones the scaler was fitted on. This silences sklearn's "valid feature
        # names" warning AND turns a silent column-order mismatch into a loud
        # error instead of a wrong prediction.
        frame_df = pd.DataFrame(vector, columns=self.feature_order)
        scaled = self.scaler.transform(frame_df)

        proba = self.model.predict_proba(scaled)[0]
        k = int(proba.argmax())
        confidence = float(proba[k])

        if confidence < self.min_prob:
            return UNCERTAIN_LABEL, confidence
        return str(self.label_encoder.classes_[k]), confidence
