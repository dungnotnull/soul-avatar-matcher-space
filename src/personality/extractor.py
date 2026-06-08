"""
Personality trait extractor using HuggingFace models.

Ingests text samples and produces Big Five (OCEAN) scores + 7-class emotion distribution.
Uses `Minej/bert-base-personality` for Big Five extraction and
`j-hartmann/emotion-english-distilroberta-base` for emotion detection.
"""

from __future__ import annotations

import numpy as np
from loguru import logger


class PersonalityExtractor:
    """
    Extracts Big Five personality scores and emotion distribution from text.
    Lazily loads models on first use to save memory when not needed.
    """

    BIG_FIVE_MODEL = "Minej/bert-base-personality"
    EMOTION_MODEL = "j-hartmann/emotion-english-distilroberta-base"
    EMOTION_LABELS = ["joy", "sadness", "anger", "fear", "surprise", "disgust", "neutral"]

    def __init__(self, device: str = "cpu"):
        self.device = device
        self._big_five_pipeline = None
        self._emotion_pipeline = None

    @property
    def big_five_pipeline(self):
        if self._big_five_pipeline is None:
            self._load_big_five()
        return self._big_five_pipeline

    @property
    def emotion_pipeline(self):
        if self._emotion_pipeline is None:
            self._load_emotion()
        return self._emotion_pipeline

    def _load_big_five(self):
        logger.info(f"Loading Big Five model: {self.BIG_FIVE_MODEL}")
        try:
            from transformers import pipeline
            self._big_five_pipeline = pipeline(
                "text-classification",
                model=self.BIG_FIVE_MODEL,
                device=-1 if self.device == "cpu" else 0,
            )
        except Exception as e:
            logger.warning(f"Failed to load Big Five model: {e}")
            self._big_five_pipeline = None

    def _load_emotion(self):
        logger.info(f"Loading emotion model: {self.EMOTION_MODEL}")
        try:
            from transformers import pipeline
            self._emotion_pipeline = pipeline(
                "text-classification",
                model=self.EMOTION_MODEL,
                device=-1 if self.device == "cpu" else 0,
                top_k=None,
            )
        except Exception as e:
            logger.warning(f"Failed to load emotion model: {e}")
            self._emotion_pipeline = None

    def extract_big_five(self, text: str) -> dict[str, float]:
        """
        Extract Big Five scores from a text sample.
        Falls back to synthetic neutral distribution if model unavailable.
        """
        if self._big_five_pipeline is None and self._big_five_pipeline is None:
            self._load_big_five()

        if self._big_five_pipeline is None:
            logger.warning("Big Five model not loaded; returning neutral scores.")
            return {"openness": 0.5, "conscientiousness": 0.5, "extraversion": 0.5,
                    "agreeableness": 0.5, "neuroticism": 0.5}

        try:
            result = self._big_five_pipeline(text[:512])
            scores = {}
            for r in result:
                label = r["label"].lower()
                scores[label] = float(r["score"])
            return {
                "openness": scores.get("openness", 0.5),
                "conscientiousness": scores.get("conscientiousness", 0.5),
                "extraversion": scores.get("extraversion", 0.5),
                "agreeableness": scores.get("agreeableness", 0.5),
                "neuroticism": scores.get("neuroticism", 0.5),
            }
        except Exception as e:
            logger.error(f"Big Five extraction failed: {e}")
            return {"openness": 0.5, "conscientiousness": 0.5, "extraversion": 0.5,
                    "agreeableness": 0.5, "neuroticism": 0.5}

    def extract_emotions(self, text: str) -> dict[str, float]:
        """Extract 7-class emotion distribution from text."""
        if self._emotion_pipeline is None and self._emotion_pipeline is None:
            self._load_emotion()

        if self._emotion_pipeline is None:
            logger.warning("Emotion model not loaded; returning neutral distribution.")
            return {"joy": 0.0, "sadness": 0.0, "anger": 0.0, "fear": 0.0,
                    "surprise": 0.0, "disgust": 0.0, "neutral": 1.0}

        try:
            result = self._emotion_pipeline(text[:512])
            if isinstance(result, list) and len(result) > 0 and isinstance(result[0], list):
                scores = {r["label"]: float(r["score"]) for r in result[0]}
            elif isinstance(result, list) and len(result) > 0:
                scores = {result[0]["label"]: float(result[0]["score"])}
            else:
                scores = {}
            return {
                "joy": scores.get("joy", 0),
                "sadness": scores.get("sadness", 0),
                "anger": scores.get("anger", 0),
                "fear": scores.get("fear", 0),
                "surprise": scores.get("surprise", 0),
                "disgust": scores.get("disgust", 0),
                "neutral": scores.get("neutral", 0),
            }
        except Exception as e:
            logger.error(f"Emotion extraction failed: {e}")
            return {"joy": 0.0, "sadness": 0.0, "anger": 0.0, "fear": 0.0,
                    "surprise": 0.0, "disgust": 0.0, "neutral": 1.0}

    def extract_full_profile(self, text: str) -> tuple[dict[str, float], dict[str, float]]:
        """Extract both Big Five and emotion scores from text in one pass."""
        big_five = self.extract_big_five(text)
        emotions = self.extract_emotions(text)
        return big_five, emotions

    def extract_batch(
        self, texts: list[str]
    ) -> tuple[list[dict[str, float]], list[dict[str, float]]]:
        """Process multiple texts and return aggregated profiles."""
        all_bf = []
        all_em = []
        for text in texts:
            bf, em = self.extract_full_profile(text)
            all_bf.append(bf)
            all_em.append(em)
        return all_bf, all_em

    @staticmethod
    def aggregate_profiles(
        big_five_list: list[dict[str, float]],
        emotion_list: list[dict[str, float]],
    ) -> tuple[dict[str, float], dict[str, float]]:
        """Average scores across multiple text windows."""
        if not big_five_list:
            return {}, {}
        traits = ["openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"]
        em_labels = ["joy", "sadness", "anger", "fear", "surprise", "disgust", "neutral"]

        avg_bf = {t: float(np.mean([bf[t] for bf in big_five_list])) for t in traits}
        avg_em = {e: float(np.mean([em[e] for em in emotion_list])) for e in em_labels}
        return avg_bf, avg_em
