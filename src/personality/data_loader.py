"""
Data loader for Siamese Network training on Big Five personality datasets.

Handles Open Psychometrics Big Five dataset, Mairesse Essays dataset,
and synthetic pair generation for compatible/incompatible labeling.
"""

from __future__ import annotations

import io
import json
import zipfile
from pathlib import Path
from dataclasses import dataclass, field
import numpy as np
import torch
from torch.utils.data import Dataset, DataLoader
from loguru import logger
import httpx

from config.settings import settings


@dataclass
class PersonalityPair:
    text_a: str
    text_b: str
    big_five_a: dict[str, float]
    big_five_b: dict[str, float]
    label: int = 1
    source: str = "unknown"


class OpenPsychometricsDataset(Dataset):
    """
    Open Psychometrics Big Five dataset — 1M+ responses with personality labels.
    Each sample: (response_text, (O,C,E,A,N)).
    """

    URL = "https://openpsychometrics.org/_rawdata/BIG5.zip"
    DATA_DIR = settings.PROJECT_ROOT / "data" / "openpsychometrics"

    def __init__(self, split: str = "train", train_ratio: float = 0.8):
        self.split = split
        self.train_ratio = train_ratio
        self.samples: list[tuple[str, list[float]]] = []
        self._ensure_downloaded()
        self._load()
        self._split_train_test()

    def _ensure_downloaded(self):
        self.DATA_DIR.mkdir(parents=True, exist_ok=True)
        csv_path = self.DATA_DIR / "data-final.csv"
        if csv_path.exists():
            return
        zip_path = self.DATA_DIR / "BIG5.zip"
        if not zip_path.exists():
            logger.info(f"Downloading Open Psychometrics Big Five dataset...")
            with httpx.stream("GET", self.URL, timeout=300, follow_redirects=True) as resp:
                resp.raise_for_status()
                with open(zip_path, "wb") as f:
                    for chunk in resp.iter_bytes(chunk_size=8192):
                        f.write(chunk)
            logger.info(f"Downloaded to {zip_path}")
        logger.info("Extracting dataset...")
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(self.DATA_DIR)
        logger.info("Extraction complete.")

    def _load(self):
        import pandas as pd
        csv_path = self.DATA_DIR / "data-final.csv"
        logger.info(f"Loading {csv_path}...")
        df = pd.read_csv(csv_path, sep="\t", low_memory=False)
        trait_cols = [c for c in df.columns if c.startswith(("O", "C", "E", "A", "N")) and len(c) > 1 and c[1:].isdigit()]
        trait_map = {}
        for col in trait_cols:
            trait = col[0]
            if trait not in trait_map:
                trait_map[trait] = []
            trait_map[trait].append(col)
        trait_names = {"O": "openness", "C": "conscientiousness", "E": "extraversion", "A": "agreeableness", "N": "neuroticism"}
        text_cols = [c for c in df.columns if "text" in c.lower() or "essay" in c.lower() or "describe" in c.lower()]
        text_col = text_cols[0] if text_cols else None
        for _, row in df.iterrows():
            scores = {}
            for trait_letter, cols in trait_map.items():
                vals = [row[c] for c in cols if pd.notna(row[c])]
                if vals:
                    scores[trait_names[trait_letter]] = float(np.mean(vals)) / 5.0
            if len(scores) == 5:
                text = str(row[text_col]) if text_col and pd.notna(row.get(text_col)) else ""
                if len(text) > 20:
                    self.samples.append((text, [
                        scores["openness"], scores["conscientiousness"],
                        scores["extraversion"], scores["agreeableness"],
                        scores["neuroticism"],
                    ]))
        logger.info(f"Loaded {len(self.samples)} valid samples.")

    def _split_train_test(self):
        np.random.seed(42)
        indices = np.random.permutation(len(self.samples))
        split_idx = int(len(self.samples) * self.train_ratio)
        if self.split == "train":
            self.indices = indices[:split_idx]
        else:
            self.indices = indices[split_idx:]

    def __len__(self):
        return len(self.indices)

    def __getitem__(self, idx):
        text, scores = self.samples[self.indices[idx]]
        return text, torch.tensor(scores, dtype=torch.float32)


class PersonalityPairDataset(Dataset):
    """
    Generates positive and negative pairs for Siamese contrastive learning.

    Positive pairs: two text windows from the same user (or very similar Big Five).
    Negative pairs: text windows from users with dissimilar Big Five profiles.
    """

    def __init__(
        self,
        samples: list[tuple[str, list[float]]],
        num_pairs: int = 50000,
        positive_ratio: float = 0.5,
        similarity_threshold: float = 0.8,
        dissimilarity_threshold: float = 0.3,
    ):
        self.samples = samples
        self.num_pairs = num_pairs
        self.scores_array = np.array([s[1] for s in samples], dtype=np.float32)
        self.positive_ratio = positive_ratio
        self.similarity_threshold = similarity_threshold
        self.dissimilarity_threshold = dissimilarity_threshold
        self._pairs = self._generate_pairs()

    def _cosine(self, a: np.ndarray, b: np.ndarray) -> float:
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-8))

    def _generate_pairs(self) -> list[PersonalityPair]:
        pairs: list[PersonalityPair] = []
        n = len(self.samples)
        num_positive = int(self.num_pairs * self.positive_ratio)
        num_negative = self.num_pairs - num_positive

        similar_pairs = 0
        attempts = 0
        while similar_pairs < num_positive and attempts < num_positive * 10:
            i, j = np.random.randint(0, n, size=2)
            if i == j:
                attempts += 1
                continue
            sim = self._cosine(self.scores_array[i], self.scores_array[j])
            if sim >= self.similarity_threshold:
                text_i, scores_i = self.samples[i]
                text_j, scores_j = self.samples[j]
                bf_i = {
                    "openness": scores_i[0], "conscientiousness": scores_i[1],
                    "extraversion": scores_i[2], "agreeableness": scores_i[3],
                    "neuroticism": scores_i[4],
                }
                bf_j = {
                    "openness": scores_j[0], "conscientiousness": scores_j[1],
                    "extraversion": scores_j[2], "agreeableness": scores_j[3],
                    "neuroticism": scores_j[4],
                }
                pairs.append(PersonalityPair(text_i, text_j, bf_i, bf_j, label=1))
                similar_pairs += 1
            attempts += 1

        logger.info(f"Generated {similar_pairs} positive pairs (target={num_positive}).")

        dissimilar_pairs = 0
        attempts = 0
        while dissimilar_pairs < num_negative and attempts < num_negative * 10:
            i, j = np.random.randint(0, n, size=2)
            if i == j:
                attempts += 1
                continue
            sim = self._cosine(self.scores_array[i], self.scores_array[j])
            if sim <= self.dissimilarity_threshold:
                text_i, scores_i = self.samples[i]
                text_j, scores_j = self.samples[j]
                bf_i = {
                    "openness": scores_i[0], "conscientiousness": scores_i[1],
                    "extraversion": scores_i[2], "agreeableness": scores_i[3],
                    "neuroticism": scores_i[4],
                }
                bf_j = {
                    "openness": scores_j[0], "conscientiousness": scores_j[1],
                    "extraversion": scores_j[2], "agreeableness": scores_j[3],
                    "neuroticism": scores_j[4],
                }
                pairs.append(PersonalityPair(text_i, text_j, bf_i, bf_j, label=0))
                dissimilar_pairs += 1
            attempts += 1

        logger.info(f"Generated {dissimilar_pairs} negative pairs (target={num_negative}).")
        np.random.shuffle(pairs)
        return pairs

    @classmethod
    def from_openpsychometrics(cls, split: str = "train", num_pairs: int = 50000) -> PersonalityPairDataset:
        ds = OpenPsychometricsDataset(split=split)
        return cls(ds.samples, num_pairs=num_pairs)

    def __len__(self):
        return len(self._pairs)

    def __getitem__(self, idx):
        pair = self._pairs[idx]
        return pair.text_a, pair.text_b, pair.label


def collate_pairs(batch: list[tuple[str, str, int]]) -> tuple[list[str], list[str], torch.Tensor]:
    texts_a, texts_b, labels = zip(*batch)
    return list(texts_a), list(texts_b), torch.tensor(labels, dtype=torch.float32)


def create_training_dataloader(
    dataset: PersonalityPairDataset,
    batch_size: int = 32,
    shuffle: bool = True,
    num_workers: int = 0,
) -> DataLoader:
    return DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=shuffle,
        num_workers=num_workers,
        collate_fn=collate_pairs,
        pin_memory=False,
    )
