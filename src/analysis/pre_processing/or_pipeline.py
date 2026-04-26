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

class OrPipeline:
    def __init__(self, path: Path, subject_id: str):
        self.subject_id = subject_id
        self.path = path
        self.eeg_path = self.path / "EEG_data" / f"subject {self.subject_id}" / "experiment"
        self.results_path = self.path / "EEG_data" / f"subject {self.subject_id}" / 'post process'
        self.fig_path = self.path / "EEG_data" / f"subject {self.subject_id}" / "figures"
        self.results_path.mkdir(parents=True, exist_ok=True)
        self.fig_path.mkdir(parents=True, exist_ok=True)

    def run(self, do_ica: bool = True, do_autoreject: bool = True, do_bad_channels: bool = True, do_auto_bad_ch: bool = False):
        raw = self._load_vhdr()
        self._resample_and_filtering(raw=raw)
        self._handle_bad_channels(raw, do_auto_bad_ch, do_bad_channels)
        epochs = self._make_epochs(raw)
        epochs = self._rereference(epochs)
        if do_autoreject:
            epochs = self._auto_reject(epochs)
        if do_ica:
            raw.filter(l_freq=1, h_freq=None) # before ICA need high pass filter
            self._do_ica(epochs)
        self._final_resample_and_filtering(epochs)
        self._save_epochs(epochs)

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

    def _handle_bad_channels(self, raw, do_auto_bad_ch: bool = True, do_bad_channels: bool = True):
        if do_auto_bad_ch:
            self._auto_detect_bad_channels(raw)
        elif do_bad_channels:
            self._manual_bad_channels(raw)

    @staticmethod
    def _make_epochs(raw):
        events_from_annot, _ = mne.events_from_annotations(raw)
        selected_events = np.array([x for x in events_from_annot if x[2] in ParallelPortDict.EVENT_DICT.values()])
        metadata, _, _ = mne.epochs.make_metadata(selected_events, event_id=ParallelPortDict.EVENT_DICT, tmin=0, tmax=0,
                                                  sfreq=raw.info['sfreq'])
        return mne.Epochs(raw, events=selected_events, event_id=ParallelPortDict.EVENT_DICT,
                          tmin=ParallelPortDict.PREPRO_ARGS['tmin'], tmax=ParallelPortDict.PREPRO_ARGS['tmax'],
                          baseline=ParallelPortDict.PREPRO_ARGS['baseline'], preload=True,
                          detrend=0, metadata=metadata, on_missing='warn')

    @staticmethod
    def _rereference(epochs):
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

    @staticmethod
    def _notch_filter(raw, freqs: float = 50.0):
        raw.notch_filter(freqs=freqs)

    @staticmethod
    def _auto_detect_bad_channels(raw):
        epochs_for_ransac = mne.make_fixed_length_epochs(raw, duration=1.0, preload=True)
        ransac = Ransac(verbose=False, n_jobs=1)
        ransac.fit(epochs_for_ransac)
        raw.info['bads'] = ransac.bad_chs_
        raw.interpolate_bads(reset_bads=True)
        logging.info(f"RANSAC: interpolated bad channels {ransac.bad_chs_}")

    @staticmethod
    def _plot_channels_for_inspection(raw, fig_path):
        eeg_picks = mne.pick_types(raw.info, eeg=True)
        info_eeg = mne.pick_info(raw.info, eeg_picks)
        data = raw.get_data(picks='eeg')
        variances = np.var(data, axis=1)
        ch_names = info_eeg.ch_names

        fig, axes = plt.subplots(2, 1, figsize=(16, 10))

        axes[0].bar(range(len(ch_names)), variances)
        axes[0].set_xticks(range(len(ch_names)))
        axes[0].set_xticklabels([f"{i}:{n}" for i, n in enumerate(ch_names)], rotation=90, fontsize=6)
        axes[0].set_ylabel('Variance (µV²)')
        axes[0].set_title('Channel Variance — outliers may be bad channels')

        mne.viz.plot_topomap(variances, info_eeg, axes=axes[1], show=False)
        axes[1].set_title('Variance Topomap')

        plt.tight_layout()
        plt.savefig(fig_path / "channel_inspection.png")
        plt.close()

        print("Channel index → name mapping:")
        for i, name in enumerate(ch_names):
            print(f"  {i}: {name}")

    def _manual_bad_channels(self, raw):
        self._plot_channels_for_inspection(raw, self.fig_path)
        raw.plot(block=True, title='Click channels to mark as bad, then close the window')
        raw.interpolate_bads(reset_bads=True)
        logging.info(f"Manual: interpolated bad channels {raw.info['bads']}")

    @staticmethod
    def _fit_ica(epochs):
        epochs_for_ica = epochs.copy().filter(l_freq=1, h_freq=None)
        ica = mne.preprocessing.ICA(method='infomax', fit_params=dict(extended=True), random_state=100)
        ica.fit(epochs_for_ica)
        return ica, epochs_for_ica

    def _do_ica(self, epochs):
        ica, epochs_for_ica = self._fit_ica(epochs)
        labels = label_components(epochs_for_ica, ica, method='iclabel')['labels']
        exclude_idx = [i for i, lbl in enumerate(labels) if lbl in ParallelPortDict.PREPRO_ARGS['drop ica']]
        ica.apply(epochs, exclude=exclude_idx)

        ica.plot_overlay(epochs.average(), exclude=exclude_idx)
        plt.savefig(self.fig_path / "ICA_Evoked_Overlay.png")
        ica.plot_components(exclude_idx)
        plt.savefig(self.fig_path / "ICA_Exclude_Comp.png")

        logging.info(f"ICA: auto rejected {exclude_idx}")

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

    @staticmethod
    def _final_resample(epochs, sfreq: float = 500.0):
        epochs.resample(sfreq)

    @staticmethod
    def _move_out_emg_electrode(raw):
        if 'EMG' in raw.ch_names:
            raw.drop_channels(['EMG'])

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
    pipe.run(do_auto_bad_ch=True)