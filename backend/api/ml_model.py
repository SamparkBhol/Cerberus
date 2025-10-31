import joblib
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import logging

logger = logging.getLogger(__name__)

MODEL_PATH = "anomaly_model.joblib"
SCALER_PATH = "scaler.joblib"

class AnomalyDetector:
    def __init__(self):
        self.model = None
        self.scaler = None
        self.is_trained = False
        self._load_model()

    def _load_model(self):
        try:
            self.model = joblib.load(MODEL_PATH)
            self.scaler = joblib.load(SCALER_PATH)
            self.is_trained = True
            logger.info("Anomaly model and scaler loaded from disk.")
        except FileNotFoundError:
            logger.info("No pre-trained model found. Model is not trained.")
            self.model = IsolationForest(contamination=0.01)
            self.scaler = StandardScaler()
            self.is_trained = False

    def _extract_features(self, packets):
        features = []
        for packet in packets:
            try:
                feat = [
                    int(packet.get('source_port', 0)),
                    int(packet.get('dest_port', 0)),
                    int(packet.get('packet_size', 0)),
                    1 if packet.get('protocol') == 'TCP' else 0,
                    1 if packet.get('protocol') == 'UDP' else 0,
                    1 if 'S' in packet.get('tcp_flags', '') else 0,
                    1 if 'F' in packet.get('tcp_flags', '') else 0,
                ]
                features.append(feat)
            except Exception as e:
                logger.warning(f"Failed to extract features from packet: {packet}, Error: {e}")
        return np.array(features)

    def train(self, packets):
        logger.info(f"Starting training with {len(packets)} packets...")
        features = self._extract_features(packets)
        if len(features) < 2:
            logger.warning("Not enough data to train model. Need at least 2 samples.")
            return False
        
        try:
            self.scaler = StandardScaler()
            scaled_features = self.scaler.fit_transform(features)
            
            self.model = IsolationForest(contamination=0.01, random_state=42)
            self.model.fit(scaled_features)
            
            joblib.dump(self.model, MODEL_PATH)
            joblib.dump(self.scaler, SCALER_PATH)
            self.is_trained = True
            logger.info("Model training complete and saved to disk.")
            return True
        except Exception as e:
            logger.error(f"Model training failed: {e}")
            return False

    def predict(self, packets):
        if not self.is_trained:
            return [], []

        features = self._extract_features(packets)
        if len(features) == 0:
            return [], []
            
        try:
            scaled_features = self.scaler.transform(features)
            predictions = self.model.predict(scaled_features)
            
            anomalous_indices = np.where(predictions == -1)[0]
            anomalous_packets = [packets[i] for i in anomalous_indices]
            return anomalous_packets, anomalous_indices
        except Exception as e:
            logger.error(f"Model prediction failed: {e}")
            return [], []

detector = AnomalyDetector()
