import logging
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import mne
from mne_icalabel import label_components
from src.analysis.enums.analysis_enums import ParallelPortDict


class ICAHandler:
    def __init__(self, fig_path: Path, save_path: Path = None):
        self.fig_path  = fig_path
        self.save_path = save_path

    def run(self, epochs: mne.Epochs) -> None:
        """Fit ICA, auto-label with ICLabel, apply, and save component figures."""
        ica, epochs_for_ica = self._fit_ica(epochs)
        self._save_ica(ica)
        ic_labels           = label_components(epochs_for_ica, ica, method='iclabel')
        labels, probs       = ic_labels['labels'], ic_labels['y_pred_proba']
        self._plot_components_labeled(ica, epochs_for_ica, labels, probs)
        exclude_idx = [i for i, lbl in enumerate(labels) if lbl in ParallelPortDict.PREPRO_ARGS['drop ica']]
        ica.apply(epochs, exclude=exclude_idx)
        ica.plot_overlay(epochs.average(), exclude=exclude_idx)
        plt.savefig(self.fig_path / "ICA_Evoked_Overlay.png"); plt.close()
        logging.info(f"ICA: auto rejected {exclude_idx}")

    def inspect(self, epochs: mne.Epochs) -> None:
        """Plot all ICA components and sources for manual inspection; print ICLabel results."""
        ica, epochs_for_ica = self._fit_ica(epochs)
        ic_labels           = label_components(epochs_for_ica, ica, method='iclabel')
        labels, probs       = ic_labels['labels'], ic_labels['y_pred_proba']
        ica.plot_components()
        plt.savefig(self.fig_path / "ICA_all_components.png"); plt.close()
        ica.plot_sources(epochs_for_ica)
        plt.savefig(self.fig_path / "ICA_sources.png"); plt.close()
        for i, (lbl, prob) in enumerate(zip(labels, probs)):
            print(f"  {i}: {lbl} ({float(np.max(np.atleast_1d(prob))):.0%} confidence)")

    def apply_manual(self, epochs: mne.Epochs, exclude_indices: list) -> None:
        """Apply ICA with manually specified component indices to exclude."""
        ica, _ = self._fit_ica(epochs)
        ica.apply(epochs, exclude=exclude_indices)
        ica.plot_overlay(epochs.average(), exclude=exclude_indices)
        plt.savefig(self.fig_path / "ICA_Evoked_Overlay.png"); plt.close()
        logging.info(f"ICA: manually rejected {exclude_indices}")

    def _save_ica(self, ica: mne.preprocessing.ICA) -> None:
        if self.save_path is None:
            return
        ica_path = self.save_path / "ica-ica.fif"
        ica.save(ica_path, overwrite=True)
        logging.info(f"ICA saved to {ica_path}")

    @staticmethod
    def _fit_ica(epochs: mne.Epochs) -> tuple:
        """Fit infomax ICA on a 1–100 Hz copy of epochs; return (ica, filtered_epochs)."""
        epochs_for_ica = epochs.copy().filter(l_freq=1, h_freq=100)
        rank = mne.compute_rank(epochs_for_ica, tol='auto', tol_kind='relative')['eeg']
        ica = mne.preprocessing.ICA(n_components=rank, method='infomax',
                                     fit_params=dict(extended=True), random_state=100)
        ica.fit(epochs_for_ica)
        return ica, epochs_for_ica

    def _plot_components_labeled(self, ica, epochs_for_ica, labels, probs) -> None:
        """Save a grid of the top-20 ICA topomaps colour-coded by ICLabel decision."""
        n_show = min(20, ica.n_components_)
        n_cols = 5
        n_rows = (n_show + n_cols - 1) // n_cols
        fig, axes = plt.subplots(n_rows, n_cols, figsize=(15, n_rows * 3))
        axes = axes.flatten()
        components = ica.get_components()
        for idx in range(n_show):
            mne.viz.plot_topomap(components[:, idx], epochs_for_ica.info, axes=axes[idx], show=False)
            lbl   = labels[idx]
            color = 'red' if lbl in ParallelPortDict.PREPRO_ARGS['drop ica'] else 'green'
            conf = float(np.max(np.atleast_1d(probs[idx])))
            axes[idx].set_title(f"IC{idx}: {lbl}\n{conf:.0%}", fontsize=8, color=color)
        for idx in range(n_show, len(axes)):
            axes[idx].set_visible(False)
        plt.suptitle("ICA Components — red=excluded, green=kept", fontsize=10)
        plt.tight_layout()
        plt.savefig(self.fig_path / "ICA_top20_labeled.png", dpi=150); plt.close()
