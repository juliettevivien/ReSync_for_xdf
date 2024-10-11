import os
from os.path import join
from mnelab.io import read_raw

from functions.io import (
    find_EEG_stream,
    write_set
)


def main_convert_xdf_to_set(
    session_ID="C002 SMTS",
    fname_external="sub-C002_ses-SMTS_control_task-Default_run-001_eeg.xdf",
):

    """
    main_convert_xdf_to_set can be used to convert .xdf file to .set files, which
    are more suitable for EEG data analysis.

    Parameters
    ----------
    session_ID: string, name of the session to be analyzed

    fname_external: string, name of the external file to be analyzed (.xdf file)

    .................................................................................

    Results
    -------
    The resulting file will be saved in the results folder, in a sub-folder named after the 
    session_ID parameter. It will be a .set file, suitable for EEG data analysis.
    """
    working_path = os.getcwd()

    #  Set saving path
    results_path = join(working_path, "results")
    saving_path = join(results_path, session_ID)
    if not os.path.isdir(saving_path):
        os.makedirs(saving_path)

    #  Set source path
    source_path = join(working_path, "sourcedata")


    #  1. LOADING DATASETS AND EXTRACT CHANNEL CONTAINING ARTIFACTS:

        ##  External data from XDF
        # load external dataset into mne
    fpath_external = join(source_path, fname_external)  
    print(f"Loading external data from {fpath_external}")
    stream_id = find_EEG_stream(fpath_external, stream_name = 'SAGA')  # find the stream_id of the EEG data, which is called 'SAGA' in our setup
    TMSi_rec = read_raw(fpath_external, stream_ids = [stream_id], preload=True)
    print(f"External data loaded from {fpath_external}")
    external_title = ("SYNCHRONIZED_EXTERNAL_" + str(fname_external[:-4]) + ".set")
    fname_external_out=join(saving_path, external_title)

    write_set(fname_external_out, TMSi_rec, TMSi_rec.annotations.onset)
    print(f"External data saved as .set file in {fname_external_out}")

if __name__ == "__main__":
     main_convert_xdf_to_set()
