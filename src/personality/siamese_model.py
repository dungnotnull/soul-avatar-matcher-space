"""
Siamese Neural Network for personality vector encoding.

Architecture: Shared BERT encoder → 512-dim L2-normalized vector.
Trained with contrastive loss to minimize distance between compatible pairs
and maximize distance between incompatible pairs.
"""

from __future__ import annotations

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from loguru import logger


class PersonalitySiameseEncoder(nn.Module):
    """
    Siamese encoder: shared BERT backbone → projection → 512-dim personality vector.
    """

    def __init__(
        self,
        backbone_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        projection_dim: int = 512,
        freeze_backbone: bool = False,
    ):
        super().__init__()
        self.backbone_name = backbone_name
        self.projection_dim = projection_dim

        try:
            from sentence_transformers import SentenceTransformer
            self.bert = SentenceTransformer(backbone_name)
            self.embedding_dim = self.bert.get_sentence_embedding_dimension()
        except Exception:
            logger.warning(f"Could not load SentenceTransformer for {backbone_name}. Using random embeddings.")
            self.bert = None
            self.embedding_dim = 384

        if freeze_backbone and self.bert is not None:
            for param in self.bert.parameters():
                param.requires_grad = False

        self.projection = nn.Sequential(
            nn.Linear(self.embedding_dim, projection_dim),
            nn.ReLU(),
            nn.Linear(projection_dim, projection_dim),
        )

    def encode(self, texts: list[str]) -> torch.Tensor:
        if self.bert is not None:
            embeddings = self.bert.encode(texts, convert_to_tensor=True)
        else:
            embeddings = torch.randn(len(texts), self.embedding_dim)
        vectors = self.projection(embeddings)
        return F.normalize(vectors, p=2, dim=1)

    def forward(self, texts_a: list[str], texts_b: list[str]) -> tuple[torch.Tensor, torch.Tensor]:
        vec_a = self.encode(texts_a)
        vec_b = self.encode(texts_b)
        return vec_a, vec_b


class ContrastiveLoss(nn.Module):
    """
    Contrastive loss: pulls similar pairs together, pushes dissimilar pairs apart.
    label=1 means compatible (should be close), label=0 means incompatible (should be far).
    """

    def __init__(self, margin: float = 0.5):
        super().__init__()
        self.margin = margin

    def forward(
        self, vec_a: torch.Tensor, vec_b: torch.Tensor, labels: torch.Tensor
    ) -> torch.Tensor:
        distances = 1.0 - F.cosine_similarity(vec_a, vec_b, dim=1)
        loss_compatible = labels * distances.pow(2)
        loss_incompatible = (1 - labels) * F.relu(self.margin - distances).pow(2)
        return loss_compatible.mean() + loss_incompatible.mean()


class TripletLoss(nn.Module):
    """Triplet loss: anchor should be closer to positive than negative by margin."""

    def __init__(self, margin: float = 0.2):
        super().__init__()
        self.margin = margin

    def forward(
        self,
        anchor: torch.Tensor,
        positive: torch.Tensor,
        negative: torch.Tensor,
    ) -> torch.Tensor:
        pos_dist = 1.0 - F.cosine_similarity(anchor, positive, dim=1)
        neg_dist = 1.0 - F.cosine_similarity(anchor, negative, dim=1)
        loss = F.relu(pos_dist - neg_dist + self.margin)
        return loss.mean()


class SiamesePersonalityModel:
    """
    High-level wrapper for training and inference with the Siamese encoder.
    """

    def __init__(
        self,
        projection_dim: int = 512,
        backbone: str = "sentence-transformers/all-MiniLM-L6-v2",
        model_path: str | None = None,
        device: str = "cpu",
    ):
        self.encoder = PersonalitySiameseEncoder(
            backbone_name=backbone,
            projection_dim=projection_dim,
        )
        self.device = device
        self.encoder.to(device)

        if model_path:
            self.load(model_path)

    def encode(self, texts: list[str]) -> np.ndarray:
        self.encoder.eval()
        with torch.no_grad():
            vectors = self.encoder.encode(texts)
        return vectors.cpu().numpy()

    def encode_single(self, text: str) -> np.ndarray:
        return self.encode([text])[0]

    def compute_similarity(self, vec_a: np.ndarray, vec_b: np.ndarray) -> float:
        """Cosine similarity between two personality vectors."""
        return float(np.dot(vec_a, vec_b) / (np.linalg.norm(vec_a) * np.linalg.norm(vec_b) + 1e-8))

    def save(self, path: str):
        torch.save(
            {
                "encoder_state": self.encoder.state_dict(),
                "projection_dim": self.encoder.projection_dim,
                "backbone_name": self.encoder.backbone_name,
            },
            path,
        )
        logger.info(f"Siamese model saved to {path}")

    def load(self, path: str):
        checkpoint = torch.load(path, map_location=self.device, weights_only=True)
        self.encoder.load_state_dict(checkpoint["encoder_state"])
        self.encoder.eval()
        logger.info(f"Siamese model loaded from {path}")
