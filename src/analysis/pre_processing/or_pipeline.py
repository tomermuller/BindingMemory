import logging
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import mne
from mne_icalabel import label_components
from autoreject import AutoReject
from src.analysis.enums.analysis_enums import ParallelPortDict
import os

class OrPipeline:
    def __init__(self, path: Path, subject_id: str):
        self.subject_id = subject_id
        self.path = path
        self.eeg_path = self.path / "EEG_data" / f"subject {self.subject_id}" / "experiment"
        self.results_path = self.path / "EEG_data" / f"subject {self.subject_id}" / 'post process'
        self.fig_path = self.path / "EEG_data" / f"subject {self.subject_id}" / "figures"

    def run(self, do_ica: bool, do_autoreject: bool):

        self.results_path.mkdir(parents=True, exist_ok=True)
        self.fig_path.mkdir(parents=True, exist_ok=True)


        vhdr_path = self.eeg_path / "BidningDecoding101.vhdr"
        raw = self._load_vhdr(vhdr_path)

        raw = raw.resample(ParallelPortDict.PREPRO_ARGS['resample'])
        if 'EMG' in raw.ch_names:
            raw.drop_channels(['EMG'])

        events_from_annot, _ = mne.events_from_annotations(raw)
        index = np.argmax(events_from_annot[:, -1] == 1)
        events_from_annot = events_from_annot[index:]

        selected_events = np.array([x for x in events_from_annot if x[2] in ParallelPortDict.EVENT_DICT.values()])
        metadata, _, _ = mne.epochs.make_metadata(selected_events, event_id=ParallelPortDict.EVENT_DICT, tmin=0, tmax=0,
                                                  sfreq=raw.info['sfreq'])
        # metadata, num_trials = add_trial_numbers(metadata, df_behav)
        # metadata = pd.merge(metadata, df_behav, on='trial_num', how='left')
        epochs = mne.Epochs(raw, events=selected_events, event_id=ParallelPortDict.EVENT_DICT,
                            tmin=ParallelPortDict.PREPRO_ARGS['tmin'], tmax=ParallelPortDict.PREPRO_ARGS['tmax'],
                            baseline=ParallelPortDict.PREPRO_ARGS['baseline'], preload=True,
                            detrend=0, metadata=metadata, on_missing='warn')

        epochs = mne.set_eeg_reference(epochs)[0]

        if do_ica:
            self._do_ica(epochs)
        if do_autoreject:
            self._auto_reject(epochs)
        # ==================== Save ====================
        ep_fname = f'{self.subject_id}_prepro-epo.fif'
        epochs.save(self.results_path / ep_fname, overwrite=True)
        logging.info(f"Epochs saved to {self.results_path / ep_fname}")

    def _do_ica(self, epochs):
        epochs_for_ica = epochs.copy().filter(l_freq=1, h_freq=None)
        ica = mne.preprocessing.ICA(method='infomax', fit_params=dict(extended=True), random_state=100)
        ica.fit(epochs_for_ica)
        labels = label_components(epochs_for_ica, ica)['labels']
        exclude_idx = [i for i, lbl in enumerate(labels) if lbl in ParallelPortDict.PREPRO_ARGS['drop ica']]
        ica.apply(epochs, exclude=exclude_idx)

        ica.plot_overlay(epochs.average(), exclude=exclude_idx)
        plt.savefig(self.fig_path / "ICA_Evoked_Overlay.png")
        ica.plot_components(exclude_idx)
        plt.savefig(self.fig_path / "ICA_Exclude_Comp.png")

        logging.info(f"ICA: rejected {exclude_idx}")

    def _load_vhdr(self, vdhr_fname, EOG_ch=False):
        """" Doc """

        raw = mne.io.read_raw_brainvision(vdhr_fname, verbose=False)

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

        epochs = epochs_ar
        logging.info(f"Autoreject: removed {len(reject_log.bad_epochs)} epochs")


def get_sub_str(sub_num):
    zeros = (3 - len(str(sub_num))) * '0'
    sub_str = f'sub_' + zeros + f'{sub_num}'
    return sub_str


def get_behav(sub_num):
    current_path = Path().absolute()

    sub_str = get_sub_str(sub_num)

    base_path = Path(__file__).resolve().parent.parent  # points to MEMORY_DECODER/
    if os.name == 'nt':
        csv_path = base_path.parent / 'EpisodicTEP' / 'Episodic-TEP-Analysis' / 'Data' / sub_str / 'Task' / f'sub{sub_num}.csv'  # Later move data into Data\raw\sub_str
    elif os.name == 'posix':
        csv_path = current_path.parent.parent / 'Episodic-TEP-Analysis' / 'Data' / sub_str / 'Task' / f'sub{sub_num}.csv'  # Later move data into Data\raw\sub_str

    df = pd.read_csv(csv_path)

    df = df.dropna()
    trials_num = df.shape[0]
    print(f'Number of valid trials: {trials_num}')

    # A dict of labels for recall column
    recall_lab = {2: 'All', 1: 'One', 0: 'None'}

    # make a new column with the number if items recalled:
    df['recall'] = df.apply(
        lambda x: recall_lab[2] if x['feat_mem'] == x['scene_mem'] and x['feat_mem'] == 'target' else '', axis=1)
    df['recall'] = df.apply(lambda x: recall_lab[1] if x['feat_mem'] != x['scene_mem'] and (
                x['feat_mem'] == 'target' or x['scene_mem'] == 'target') else x['recall'], axis=1)
    df['recall'] = df['recall'].replace('', recall_lab[0])

    # Get thier idx
    # correct =  df.index[(df.feat_mem == 'target')] & df.index[(df.scene_mem == 'target')] .tolist()
    # correct_certai
    # n= df.index[(df.feat_mem == 'target')] & df.index[(df.scene_mem == 'target')] & df.index[(df['con_score'] == 'certain')]
    count_feat_mem = df.feat_mem.value_counts()

    feat_mem = count_feat_mem.target / (count_feat_mem.target + count_feat_mem.lure)
    return df


def add_trial_numbers(metadata, df_behav):
    trial_num = 0
    trial_numbers = []

    for event in metadata['event_name']:
        if event.startswith('baseline'):
            trial_num += 1
        trial_numbers.append(trial_num)

    metadata['trial_num'] = trial_numbers
    metadata.loc[metadata['event_name'] == 'retrieval', 'trial_num'] = None
    df_behav_ret_sort = df_behav.sort_values(by='trl_no_ret')
    retrieval_metadata = metadata[metadata['event_name'] == 'retrieval']
    metadata.loc[retrieval_metadata.index, 'trial_num'] = list(df_behav_ret_sort['trial_num'])
    return metadata, max(trial_numbers)


if __name__ == '__main__':
    data_path = "/Users/tomermuller/Desktop/data/"
    subject_str = "101"