import logging
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import mne
from mne_icalabel import label_components
from autoreject import AutoReject, Ransac
from src.analysis.enums.analysis_enums import ParallelPortDict
import os
from PyQt5.QtWidgets import QApplication, QInputDialog

class OrPipeline:
    def __init__(self, path: Path, subject_id: str):
        self.subject_id = subject_id
        self.path = path
        self.eeg_path = self.path / "EEG_data" / f"subject {self.subject_id}" / "experiment"
        self.results_path = self.path / "EEG_data" / f"subject {self.subject_id}" / 'post process'
        self.fig_path = self.path / "EEG_data" / f"subject {self.subject_id}" / "figures"
        self.results_path.mkdir(parents=True, exist_ok=True)
        self.fig_path.mkdir(parents=True, exist_ok=True)

    def run(self, do_ica: bool = True):
        log_path = self.results_path / f"{self.subject_id}_preprocessing.log"
        file_handler = logging.FileHandler(log_path)
        file_handler.setLevel(logging.INFO)
        logging.getLogger().addHandler(file_handler)

        raw = self._load_vhdr()
        self._resample_and_filtering(raw=raw)
        self._handle_bad_channels(raw)
        self._log_event_counts(raw)
        # save here the raw
        epochs = self._make_epochs(raw)
        # save the epochs
        epochs = self._rereference(epochs)
        epochs = self._auto_reject(epochs)
        # save
        if do_ica:
            raw.filter(l_freq=1, h_freq=None)
            self._do_ica(epochs)
        self._final_resample_and_filtering(epochs)
        self._save_epochs(epochs)

        logging.getLogger().removeHandler(file_handler)
        file_handler.close()

    def _load_vhdr(self, EOG_ch=False):
        """" Doc """
        vhdr_path = self.eeg_path / f"Bindingdecoding{self.subject_id}.vhdr"
        raw = mne.io.read_raw_brainvision(vhdr_path, verbose=False)
        raw.load_data()

        # set channel type for EMG and EOG
        raw.set_channel_types({"EMG": 'emg'})

        if 'HEGOC' in raw.ch_names:
            raw.rename_channels({'HEGOC': 'HEOG'})

        if EOG_ch == True:
            raw.set_channel_types({"HEOG": 'eog', "VEOG": 'eog'})

        # Set montage
        montage = mne.channels.make_standard_montage('easycap-M1')  #

        # Find AFz in the montage and change it so it matches the true label "Afz" (f instead of F)
        i = montage.ch_names.index("AFz")
        montage.ch_names[i] = "Afz"

        raw.set_montage(montage, verbose=False)

        return raw

    def _resample_and_filtering(self, raw):
        self._move_out_emg_electrode(raw)
        self._high_pass_filter(raw)
        self._notch_filter(raw)
        raw.resample(ParallelPortDict.PREPRO_ARGS['resample'])
        logging.info(f"Resampled to {ParallelPortDict.PREPRO_ARGS['resample']} Hz")

    def _handle_bad_channels(self, raw):
        raw.plot(block=True)  # inspect channels — close this window to proceed
        app = QApplication.instance() or QApplication([])
        text, ok = QInputDialog.getText(None, "Bad Channels", "Enter bad channel names separated by commas (e.g. Fp1,Cz):")
        bad_channels = [ch.strip() for ch in text.split(',') if ch.strip()] if ok else []
        raw.info['bads'] = bad_channels
        raw.interpolate_bads(reset_bads=True)
        logging.info(f"Manual: interpolated bad channels {bad_channels}")
        print(f"Interpolated bad channels: {bad_channels}")

    @staticmethod
    def _log_event_counts(raw):
        id_to_name = {v: k for k, v in ParallelPortDict.EVENT_DICT.items()}
        events, _ = mne.events_from_annotations(raw, verbose=False)
        unique, counts = np.unique(events[:, 2], return_counts=True)
        logging.info("--- Trigger counts ---")
        print("--- Trigger counts ---")
        for event_id, count in zip(unique, counts):
            name = id_to_name.get(event_id, f"unknown ({event_id})")
            msg = f"  [{event_id:>3}] {name}: {count}"
            logging.info(msg)
            print(msg)
        logging.info("----------------------")
        print("----------------------")

    @staticmethod
    def _make_epochs(raw):
        events_from_annot, _ = mne.events_from_annotations(raw)
        selected_events = np.array([x for x in events_from_annot if x[2] in ParallelPortDict.EVENT_DICT.values()])
        logging.info(f"Found {len(selected_events)} events for epoching (tmin={ParallelPortDict.PREPRO_ARGS['tmin']}, tmax={ParallelPortDict.PREPRO_ARGS['tmax']})")
        metadata, _, _ = mne.epochs.make_metadata(selected_events, event_id=ParallelPortDict.EVENT_DICT, tmin=0, tmax=0,
                                                  sfreq=raw.info['sfreq'])
        return mne.Epochs(raw, events=selected_events, event_id=ParallelPortDict.EVENT_DICT,
                          tmin=ParallelPortDict.PREPRO_ARGS['tmin'], tmax=ParallelPortDict.PREPRO_ARGS['tmax'],
                          baseline=ParallelPortDict.PREPRO_ARGS['baseline'], preload=True,
                          detrend=0, metadata=metadata, on_missing='warn')

    @staticmethod
    def _rereference(epochs):
        logging.info("Applying average reference")
        return mne.set_eeg_reference(epochs)[0]

    def _final_resample_and_filtering(self, epochs):
        self._low_pass_filter(epochs)
        self._final_resample(epochs)

    def _save_epochs(self, epochs):
        ep_fname = f'{self.subject_id}_prepro-epo.fif'
        epochs.save(self.results_path / ep_fname, overwrite=True)
        logging.info(f"Epochs saved to {self.results_path / ep_fname}")

    def plot_signal_snapshot(self, data, step_name: str):
        fig, axes = plt.subplots(1, 2, figsize=(16, 4))

        psd = data.compute_psd()
        psd.plot(axes=axes[0], show=False)
        axes[0].set_title(f'PSD — {step_name}')

        if isinstance(data, mne.io.BaseRaw):
            segment = data.get_data(picks='eeg', start=0, stop=int(data.info['sfreq'] * 10))
            times = np.linspace(0, 10, segment.shape[1])
        else:
            segment = data.get_data(picks='eeg').mean(axis=0)
            times = data.times

        axes[1].plot(times, segment.T, color='steelblue', alpha=0.3, linewidth=0.5)
        axes[1].set_xlabel('Time (s)')
        axes[1].set_ylabel('Amplitude (V)')
        axes[1].set_title(f'Signal — {step_name}')

        plt.tight_layout()
        plt.savefig(self.fig_path / f"snapshot_{step_name.replace(' ', '_')}.png")
        plt.close()

    @staticmethod
    def _high_pass_filter(raw, l_freq: float = 0.1):
        raw.filter(l_freq=l_freq, h_freq=None)
        logging.info(f"High-pass filter applied: {l_freq} Hz")

    @staticmethod
    def _notch_filter(raw, freqs: float = 50.0):
        raw.notch_filter(freqs=freqs)
        logging.info(f"Notch filter applied: {freqs} Hz")

    @staticmethod
    def _fit_ica(epochs):
        epochs_for_ica = epochs.copy().filter(l_freq=1, h_freq=None)
        ica = mne.preprocessing.ICA(method='infomax', fit_params=dict(extended=True), random_state=100)
        ica.fit(epochs_for_ica)
        return ica, epochs_for_ica

    def _do_ica(self, epochs):
        ica, epochs_for_ica = self._fit_ica(epochs)
        ic_labels = label_components(epochs_for_ica, ica, method='iclabel')
        labels = ic_labels['labels']
        probs = ic_labels['y_pred_proba']

        self._plot_ica_components_labeled(ica, epochs_for_ica, labels, probs)

        exclude_idx = [i for i, lbl in enumerate(labels) if lbl in ParallelPortDict.PREPRO_ARGS['drop ica']]
        ica.apply(epochs, exclude=exclude_idx)

        ica.plot_overlay(epochs.average(), exclude=exclude_idx)
        plt.savefig(self.fig_path / "ICA_Evoked_Overlay.png")
        plt.close()

        logging.info(f"ICA: auto rejected {exclude_idx}")

    def _plot_ica_components_labeled(self, ica, epochs_for_ica, labels, probs):
        n_show = min(20, ica.n_components_)
        n_cols = 5
        n_rows = (n_show + n_cols - 1) // n_cols
        fig, axes = plt.subplots(n_rows, n_cols, figsize=(15, n_rows * 3))
        axes = axes.flatten()

        components = ica.get_components()
        for idx in range(n_show):
            mne.viz.plot_topomap(components[:, idx], epochs_for_ica.info, axes=axes[idx], show=False)
            lbl = labels[idx]
            conf = max(probs[idx])
            color = 'red' if lbl in ParallelPortDict.PREPRO_ARGS['drop ica'] else 'green'
            axes[idx].set_title(f"IC{idx}: {lbl}\n{conf:.0%}", fontsize=8, color=color)

        for idx in range(n_show, len(axes)):
            axes[idx].set_visible(False)

        plt.suptitle("ICA Components — red=excluded, green=kept", fontsize=10)
        plt.tight_layout()
        plt.savefig(self.fig_path / "ICA_top20_labeled.png", dpi=150)
        plt.close()

    def _plot_ica_for_inspection(self, epochs):
        ica, epochs_for_ica = self._fit_ica(epochs)
        ic_labels = label_components(epochs_for_ica, ica, method='iclabel')

        labels = ic_labels['labels']
        probs = ic_labels['y_pred_proba']

        ica.plot_components()
        plt.savefig(self.fig_path / "ICA_all_components.png")
        plt.close()

        ica.plot_sources(epochs_for_ica)
        plt.savefig(self.fig_path / "ICA_sources.png")
        plt.close()

        print("ICA component index → ICLabel classification:")
        for i, (lbl, prob) in enumerate(zip(labels, probs)):
            print(f"  {i}: {lbl} ({max(prob):.0%} confidence)")

    def _manual_ica(self, epochs, exclude_indices: list):
        ica, _ = self._fit_ica(epochs)
        ica.apply(epochs, exclude=exclude_indices)

        ica.plot_overlay(epochs.average(), exclude=exclude_indices)
        plt.savefig(self.fig_path / "ICA_Evoked_Overlay.png")
        plt.close()

        logging.info(f"ICA: manually rejected {exclude_indices}")

    @staticmethod
    def _low_pass_filter(epochs, h_freq: float = 100.0):
        epochs.filter(l_freq=None, h_freq=h_freq)
        logging.info(f"Low-pass filter applied: {h_freq} Hz")

    @staticmethod
    def _final_resample(epochs, sfreq: float = 500.0):
        epochs.resample(sfreq)
        logging.info(f"Final resample to {sfreq} Hz")

    @staticmethod
    def _move_out_emg_electrode(raw):
        if 'EMG' in raw.ch_names:
            raw.drop_channels(['EMG'])
            logging.info("Dropped channel: EMG")
        else:
            logging.info("No EMG channel found, skipping")

    def _auto_reject(self, epochs):
        ar = AutoReject(n_jobs=1, random_state=11, n_interpolate=[1, 2, 3, 4])
        ar.fit(epochs[:100])
        epochs_ar, reject_log = ar.transform(epochs, return_log=True)

        fig = epochs[reject_log.bad_epochs].plot(scalings=dict(eeg=100e-6))
        try:
            fig.grab().save(str(self.fig_path / "Autoreject_Bad_Epochjs.png"))
        except Exception as e:
            print(f"Skipping grab() save due to: {e}")
        reject_log.plot('horizontal')
        plt.savefig(self.fig_path / "Autoreject_Reject_LOG")

        logging.info(f"Autoreject: removed {sum(reject_log.bad_epochs)} epochs")
        return epochs_ar


if __name__ == '__main__':
    data_path = Path("/Users/tomermuller/Desktop/data/")
    subject_str = "102"
    pipe = OrPipeline(path = data_path, subject_id=subject_str)
    pipe.run()