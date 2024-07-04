import os
from os.path import join
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from mnelab.io import read_raw
import mne
from copy import deepcopy



from functions.io import (
    load_mat_file,
    find_EEG_stream,
    load_intracranial_artifact_channel,
    load_xdf_artifact_channel,
    write_set
)
from functions.plotting import (
    plot_LFP_external, 
    ecg, 
    xdf_plot_lfp_external
)
from functions.utils import (
    _update_and_save_params, 
    _update_and_save_multiple_params, 
    _get_input_y_n, 
    _get_user_input,
    _check_for_empties,
    _get_onedrive_path
)
from functions.find_artifacts import (
    detect_artifacts_in_external_recording,
    detect_artifacts_in_intracranial_recording
)
from functions.timeshift import check_timeshift


def main_xdf_batch(
    excel_fname = "WP3_rec_info.xlsx",
    CHECK_FOR_TIMESHIFT=True
):

    """
    main_xdf_batch.py is the main function of ReSync_for_xdf for performing multiple session 
    synchronization.

    Parameters
    ----------
    excel_fname: str, name of the excel file containing the information about the recordings

    CHECK_FOR_TIMESHIFT: boolean, if True, perform timeshift analysis

    .................................................................................

    Results
    -------
    The results will be saved in the results folder, in a sub-folder named after the 
    session_ID parameter.
    8 figures are automatically generated and saved:
    - Fig 1: External bipolar channel raw plot (of the channel containing artifacts)
    - Fig 2: External bipolar channel with artifact detected
    - Fig 3: External bipolar channel - first artifact detected (zoom of Fig2)
    - Fig 4: Intracranial channel raw plot (of the channel containing artifacts)
    - Fig 5 : Intracranial channel with artifact detected - method ID (indicates which 
    kernel was used to detect the artifact properly)
    - Fig 6: Intracranial channel - first artifact detected - method ID (zoom of Fig5)
    - (Fig 7:Intracranial channel - first artifact corrected by user)
    Fig 7 is only generated when no automatic detection of the artifact was possible,
    and the user therefore had to manually select it (rare cases)
    - Fig 8: Intracranial and external recordings aligned

    IF the timeshift analysis is also performed, there will be one supplementary figure:
    - Fig A : Timeshift - Intracranial and external recordings aligned - last artifact

    """

    onedrivepath = _get_onedrive_path()
    excel_file_path = join(onedrivepath, excel_fname)
    df = pd.read_excel(excel_file_path, sheet_name="Recording Information")

    # Loop for all recording sessions present in the file provided,
    # analyze one by one:
    for index, row in df.iterrows():
        done = row['Synced']
        if done == "yes":
            continue
        else:
            session_ID = row['session ID']
            fname_lfp = row['extracted mat files']
            fname_external = row['LSL filename']
            sync_side = row['sync side']
            BIP_ch_name = row['IPG BIP']

        SKIP = _check_for_empties(session_ID, fname_lfp, fname_external, sync_side, BIP_ch_name, index)
        if SKIP:
            continue
        if session_ID[0] == "C":
            print(f"Skipping control session " + session_ID + " ...")
            continue
        if sync_side == "left":
            ch_idx_lfp = 0
        elif sync_side == "right":
            ch_idx_lfp = 1

        """
        working_path = os.getcwd()

        #  Set saving path
        results_path = join(working_path, "results")
        saving_path = join(results_path, session_ID)
        if not os.path.isdir(saving_path):
            os.makedirs(saving_path)

        #  Set source path
        source_path = join(working_path, "sourcedata")
        """

        # Set sourcepath and saving path:
        subject_path = join(onedrivepath, session_ID[:5])
        raw_data_path = join(subject_path, "raw_data")
        pre_lfp_source_path = join(raw_data_path, "JSON")
        lfp_source_path = join(pre_lfp_source_path, session_ID[7:12])
        pre_external_source_path = join(raw_data_path, "XDF")
        external_source_path = join(pre_external_source_path, session_ID[7:12])

        results_path = join(subject_path, "synced_data")
        if not os.path.isdir(results_path):
            os.makedirs(results_path)
        saving_path = join(results_path, session_ID)
        if not os.path.isdir(saving_path):
            os.makedirs(saving_path)

        #  1. LOADING DATASETS AND EXTRACT CHANNEL CONTAINING ARTIFACTS:
            ##  Intracranial LFP
        lfp_rec = load_mat_file(
                session_ID=session_ID,
                filename=fname_lfp,
                saving_path=saving_path,
                source_path=lfp_source_path,
            )
        sf_LFP = lfp_rec.info["sfreq"] # sampling frequency of intracranial recording
        dictionary = {"SF_INTERNAL": sf_LFP, "CH_IDX_LFP": ch_idx_lfp}
        _update_and_save_multiple_params(dictionary, session_ID, saving_path)
        lfp_sig = load_intracranial_artifact_channel(lfp_rec, ch_idx_lfp)

        
            ##  External data from XDF
            # load external dataset into mne
        _update_and_save_params("FNAME_EXTERNAL", fname_external, session_ID, saving_path)
        fpath_external = join(external_source_path, fname_external)  
        stream_id = find_EEG_stream(fpath_external, stream_name = 'SAGA')  # find the stream_id of the EEG data, which is called 'SAGA' in our setup
        TMSi_rec = read_raw(fpath_external, stream_ids = [stream_id], preload=True)
        sf_external_LSL = (TMSi_rec.info["sfreq"]) # sampling frequency of external recording
        sf_external = round(sf_external_LSL)  # handle cases when the sf_external is not an integer (as it should be by definition during the recording itself)
        BIP_channel, ch_index_external = load_xdf_artifact_channel(TMSi_rec, BIP_ch_name, session_ID,saving_path)
        dictionary = {"SF_EXTERNAL_LSL": sf_external_LSL, "SF_EXTERNAL": sf_external, "CH_IDX_EXTERNAL": ch_index_external}
        _update_and_save_multiple_params(dictionary, session_ID, saving_path)

        
        #  2. FIND ARTIFACTS IN BOTH RECORDINGS:
            # 2.1. Find artifacts in external recording:
        art_start_BIP = detect_artifacts_in_external_recording(
            session_ID=session_ID,
            BIP_channel=BIP_channel,
            sf_external=sf_external,
            saving_path=saving_path,
            start_index=0,
        )
        artifact_correct = _get_input_y_n(
            "Is the external DBS artifact properly selected ? "
        )
        
        if artifact_correct in ("y", "Y"):
            _update_and_save_params(
                key="ART_TIME_BIP",
                value=art_start_BIP,
                session_ID=session_ID,
                saving_path=saving_path
            )
        else:
            # if there's an unrelated artifact or if the stimulation is ON at the beginning
            # of the recording, the user can input the number of seconds to ignore at the
            # beginning of the recording, and the function will start looking for artifacts
            # after that time.
            start_later = _get_user_input(
                "How many seconds in the beginning should be ignored "
            )
            start_later_index = start_later * sf_external
            art_start_BIP = detect_artifacts_in_external_recording(
                session_ID=session_ID,
                BIP_channel=BIP_channel,
                sf_external=sf_external,
                saving_path=saving_path,
                start_index=round(start_later_index),
            )
            _update_and_save_params(
                key="ART_TIME_BIP",
                value=art_start_BIP,
                session_ID=session_ID,
                saving_path=saving_path,
            )

        

            # 2.2. Find artifacts in intracranial recording:
        methods = ["thresh", "2", "1", "manual"]
        # thresh takes the last sample that lies within the value distribution of the 
            # thres_window (aka: baseline window) before the threshold passing
        # kernel 1 only searches for the steep decrease
        # kernel 2 is more custom and takes into account the steep decrease and slow recover
        # manual kernel is for none of the three previous methods work. Then the artifact
            # has to be manually selected by the user, in a pop up window that will automatically open.
        for method in methods:
            print("Running resync with method = {}...".format(method))
            art_start_LFP = detect_artifacts_in_intracranial_recording(
                session_ID=session_ID,
                lfp_sig=lfp_sig,
                sf_LFP=sf_LFP,
                saving_path=saving_path,
                method=method
            )

            artifact_correct = _get_input_y_n(
                "Is the intracranial DBS artifact properly selected ? "
            )
            if artifact_correct in ("y","Y"):
                dictionary = {"ART_TIME_LFP": art_start_LFP, "METHOD": method}
                _update_and_save_multiple_params(dictionary,session_ID,saving_path)
                break
            else: 
                skip_beginning = _get_input_y_n(
                "Do you want to skip the beginning of the recording ? "
            )
                if skip_beginning in ("y", "Y"):
                    start_later = _get_user_input(
                        "How many seconds in the beginning should be ignored "
                    )
                    start_later_index = start_later * round(sf_LFP)
                    print("start_later_index", start_later_index)            
                    art_start_LFP = detect_artifacts_in_intracranial_recording(
                        session_ID=session_ID,
                        lfp_sig=lfp_sig,
                        sf_LFP=sf_LFP,
                        saving_path=saving_path,
                        method=method,
                        start_index=start_later_index,
                    )
                    dictionary = {"ART_TIME_LFP": art_start_LFP, "METHOD": method}
                    _update_and_save_multiple_params(dictionary,session_ID,saving_path)
                    break


        # 3. SYNCHRONIZE AND SAVE RECORDINGS:
        ## detect events in external dataset
        events, _ = mne.events_from_annotations(TMSi_rec)
        inv_dic = {v: k for k, v in _.items()}

        ## offset intracranial recording (crop everything that is more than 1s before the artifact)
        tmax_lfp = max(lfp_rec.times)
        new_start_intracranial = art_start_LFP - 1
        lfp_rec_offset = lfp_rec.copy().crop(tmin=new_start_intracranial, tmax=tmax_lfp)
        #lfp_rec_offset.plot(title="lfp_rec_offset")

        ## offset external recording (crop everything that is more than 1s before the artifact)
        tmax_external = max(TMSi_rec.times)
        new_start_external = art_start_BIP - 1
        TMSi_rec_offset = TMSi_rec.copy().crop(tmin=new_start_external, tmax=tmax_external)
        #TMSi_rec_offset.plot(title='TMSi_rec_offset')

        ## transfer of the events from the external to the intracranial recording
        # create a duplicate of the events to manipulate it without changing the external one
        events_lfp = deepcopy(events)

        # get the events from the external in time instead of samples to account for the different sampling frequencies
        events_in_time = events[:,0]/sf_external

        # then offset the events in time to the new start of the external recording
        events_in_time_offset = events_in_time - new_start_external

        # convert the events in time offset to samples corresponding to the sampling frequency of the intracranial recording
        # because the annotations object works with samples, not timings
        events_in_time_offset_lfp = events_in_time_offset * sf_LFP
        events_lfp[:,0] = events_in_time_offset_lfp

        ## create an annotation object for the intracranial recording
        annotations_lfp = mne.annotations_from_events(events_lfp, sfreq=sf_LFP, event_desc=inv_dic)

        lfp_rec_offset.set_annotations(None) # make sure that no annotations are present
        lfp_rec_offset.set_annotations(annotations_lfp) # set the new annotations

        external_title = ("SYNCHRONIZED_EXTERNAL_" + str(fname_external[:-4]) + ".set")
        fname_external_out=join(saving_path, external_title)
        TMSi_rec_offset_annotations_onset= (TMSi_rec_offset.annotations.onset) - new_start_external
        lfp_title = ("SYNCHRONIZED_INTRACRANIAL_" + str(fname_lfp[:-4]) + ".set")
        fname_lfp_out =join(saving_path, lfp_title)
        lfp_rec_offset_annotations_onset= (lfp_rec_offset.annotations.onset) - new_start_intracranial

        write_set(fname_external_out, TMSi_rec_offset, TMSi_rec_offset_annotations_onset)
        write_set(fname_lfp_out, lfp_rec_offset, lfp_rec_offset_annotations_onset)

        # 5. PLOT SYNCHRONIZED RECORDINGS:
        xdf_plot_lfp_external(TMSi_rec_offset, lfp_rec_offset, ch_index_external, ch_idx_lfp, sf_LFP, sf_external, saving_path, session_ID)

        """
        plot_LFP_external(
            session_ID=session_ID,
            LFP_synchronized=LFP_synchronized,
            external_synchronized=external_synchronized,
            sf_LFP=sf_LFP,
            sf_external=sf_external,
            ch_idx_lfp=ch_idx_lfp,
            ch_index_external=ch_index_external,
            saving_path=saving_path,
        )

        """
        #  OPTIONAL : check timeshift:
        if CHECK_FOR_TIMESHIFT:
            print("Starting timeshift analysis...")
            external_synchronized = TMSi_rec_offset.get_data()
            LFP_synchronized = lfp_rec_offset.get_data()
            check_timeshift(
                session_ID=session_ID,
                LFP_synchronized=LFP_synchronized,
                sf_LFP=sf_LFP,
                external_synchronized=external_synchronized,
                sf_external=sf_external,
                saving_path=saving_path,
            )
    

if __name__ == "__main__":
    main_xdf_batch()
