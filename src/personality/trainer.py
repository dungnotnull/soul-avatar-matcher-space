"""
Siamese Network training orchestration.

Trains the PersonalitySiameseEncoder on Big Five labeled pairs using
contrastive loss. Handles checkpointing, early stopping, and metrics.
"""

from __future__ import annotations

import time
import numpy as np
import torch
from torch.utils.data import DataLoader
from torch.optim import AdamW
from torch.optim.lr_scheduler import CosineAnnealingLR
from loguru import logger

from src.personality.siamese_model import PersonalitySiameseEncoder, ContrastiveLoss
from src.personality.data_loader import PersonalityPairDataset, create_training_dataloader


class SiameseTrainer:
    def __init__(
        self,
        encoder: PersonalitySiameseEncoder | None = None,
        device: str = "cpu",
        lr: float = 2e-5,
        weight_decay: float = 0.01,
        margin: float = 0.5,
        epochs: int = 10,
        batch_size: int = 32,
        validation_split: float = 0.15,
        early_stopping_patience: int = 3,
        checkpoint_dir: str = "models",
    ):
        self.device = device
        self.encoder = encoder or PersonalitySiameseEncoder().to(device)
        self.loss_fn = ContrastiveLoss(margin=margin)
        self.optimizer = AdamW(
            [p for p in self.encoder.parameters() if p.requires_grad],
            lr=lr,
            weight_decay=weight_decay,
        )
        self.scheduler = CosineAnnealingLR(self.optimizer, T_max=epochs)
        self.epochs = epochs
        self.batch_size = batch_size
        self.validation_split = validation_split
        self.early_stopping_patience = early_stopping_patience
        self.checkpoint_dir = checkpoint_dir
        self.train_losses: list[float] = []
        self.val_losses: list[float] = []
        self.val_accuracies: list[float] = []

    def train(self, dataset: PersonalityPairDataset | None = None) -> dict:
        if dataset is None:
            logger.info("Loading Open Psychometrics dataset...")
            dataset = PersonalityPairDataset.from_openpsychometrics(
                split="train", num_pairs=50000
            )

        val_size = int(len(dataset) * self.validation_split)
        train_size = len(dataset) - val_size
        train_ds, val_ds = torch.utils.data.random_split(
            dataset, [train_size, val_size],
            generator=torch.Generator().manual_seed(42),
        )

        train_loader = DataLoader(
            train_ds, batch_size=self.batch_size, shuffle=True,
            collate_fn=self._collate_fn, drop_last=True,
        )
        val_loader = DataLoader(
            val_ds, batch_size=self.batch_size, shuffle=False,
            collate_fn=self._collate_fn,
        )

        logger.info(f"Training on {train_size} pairs, validating on {val_size} pairs, {self.epochs} epochs.")
        best_val_loss = float("inf")
        patience_counter = 0

        for epoch in range(self.epochs):
            start = time.time()
            train_loss = self._train_epoch(train_loader)
            val_loss, val_acc = self._validate(val_loader)

            self.train_losses.append(train_loss)
            self.val_losses.append(val_loss)
            self.val_accuracies.append(val_acc)

            self.scheduler.step()
            elapsed = time.time() - start

            logger.info(
                f"Epoch {epoch+1}/{self.epochs} | "
                f"train_loss={train_loss:.4f} | val_loss={val_loss:.4f} | "
                f"val_acc={val_acc:.3f} | lr={self.scheduler.get_last_lr()[0]:.2e} | "
                f"time={elapsed:.1f}s"
            )

            if val_loss < best_val_loss:
                best_val_loss = val_loss
                patience_counter = 0
                self._save_checkpoint(epoch, val_loss, val_acc, is_best=True)
            else:
                patience_counter += 1
                if patience_counter >= self.early_stopping_patience:
                    logger.info(f"Early stopping at epoch {epoch+1}")
                    break

        self._save_final()
        return {
            "epochs_completed": epoch + 1,
            "best_val_loss": best_val_loss,
            "best_val_accuracy": max(self.val_accuracies),
            "final_train_loss": self.train_losses[-1],
        }

    def _train_epoch(self, loader: DataLoader) -> float:
        self.encoder.train()
        total_loss = 0.0
        for batch_idx, (texts_a, texts_b, labels) in enumerate(loader):
            labels = labels.to(self.device)
            self.optimizer.zero_grad()
            vec_a, vec_b = self.encoder(texts_a, texts_b)
            loss = self.loss_fn(vec_a, vec_b, labels)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(self.encoder.parameters(), 1.0)
            self.optimizer.step()
            total_loss += loss.item()
        return total_loss / len(loader)

    def _validate(self, loader: DataLoader) -> tuple[float, float]:
        self.encoder.eval()
        total_loss = 0.0
        correct = 0
        total = 0
        with torch.no_grad():
            for texts_a, texts_b, labels in loader:
                labels = labels.to(self.device)
                vec_a, vec_b = self.encoder(texts_a, texts_b)
                loss = self.loss_fn(vec_a, vec_b, labels)
                total_loss += loss.item()
                similarities = torch.nn.functional.cosine_similarity(vec_a, vec_b)
                preds = (similarities > 0.5).float()
                correct += (preds == labels).sum().item()
                total += labels.size(0)
        return total_loss / len(loader), correct / max(total, 1)

    def _save_checkpoint(self, epoch: int, val_loss: float, val_acc: float, is_best: bool = False):
        import os
        os.makedirs(self.checkpoint_dir, exist_ok=True)
        checkpoint = {
            "epoch": epoch,
            "encoder_state": self.encoder.state_dict(),
            "optimizer_state": self.optimizer.state_dict(),
            "scheduler_state": self.scheduler.state_dict(),
            "val_loss": val_loss,
            "val_accuracy": val_acc,
            "train_losses": self.train_losses,
            "projection_dim": self.encoder.projection_dim,
            "backbone_name": self.encoder.backbone_name,
        }
        path = f"{self.checkpoint_dir}/checkpoint_epoch{epoch+1}.pt"
        torch.save(checkpoint, path)
        if is_best:
            best_path = f"{self.checkpoint_dir}/best_model.pt"
            torch.save(checkpoint, best_path)
            logger.info(f"Best model saved to {best_path}")

    def _save_final(self):
        path = f"{self.checkpoint_dir}/siamese_personality_v1.pt"
        self.encoder.eval()
        checkpoint = {
            "encoder_state": self.encoder.state_dict(),
            "projection_dim": self.encoder.projection_dim,
            "backbone_name": self.encoder.backbone_name,
            "train_losses": self.train_losses,
            "val_losses": self.val_losses,
            "val_accuracies": self.val_accuracies,
        }
        torch.save(checkpoint, path)
        logger.info(f"Final model exported to {path}")

    @staticmethod
    def _collate_fn(batch):
        texts_a, texts_b, labels = [], [], []
        for item in batch:
            texts_a.append(item[0])
            texts_b.append(item[1])
            labels.append(item[2])
        return texts_a, texts_b, torch.tensor(labels, dtype=torch.float32)


def train_siamese_model(
    dataset_path: str | None = None,
    epochs: int = 10,
    batch_size: int = 32,
    device: str = "cpu",
    output_path: str = "models/siamese_personality_v1.pt",
) -> dict:
    encoder = PersonalitySiameseEncoder().to(device)
    trainer = SiameseTrainer(
        encoder=encoder,
        epochs=epochs,
        batch_size=batch_size,
        device=device,
        checkpoint_dir="models",
    )
    dataset = None
    if dataset_path and Path(dataset_path).exists():
        dataset = PersonalityPairDataset.from_openpsychometrics(split="train")
    else:
        dataset = PersonalityPairDataset.from_openpsychometrics(split="train", num_pairs=50000)
    metrics = trainer.train(dataset)
    return metrics
