# ReSync_for_xdf

## About
ReSync is an open-access tool to align intracerebral recordings (from DBS electrodes) with external recordings. A manuscript describing ReSync's functionality and methodology will follow. This repo is derived from the original ReSync repo (https://github.com/MovDisBerlin/ReSync), and has been adapted to make it compatible with xdf file formats. This is useful in the case of data acquisition with LabStreaming Layer (https://github.com/labstreaminglayer/App-LabRecorder/releases). 

This repo is structured as follows: 

```
.
├── results
├── scripts
    ├── functions
    │   ├── find_artifacts
    │   ├── interactive
    │   ├── io
    │   ├── plotting
    │   ├── timeshift
    │   ├── tmsi_poly5reader
    │   └── utils
    ├── pyxdftools
    ├── main_xdf
    ├── main_xdf_batch
    └── resync_xdf_notebook
├── sourcedata
├── environment.yml
├── LICENSE.txt
├── README.md
└── setup.py
```

```environment.yml``` contains all the packages and their version needed to run the ReSync algorithm.
```main_xdf``` and ```main_xdf_batch``` are the two main scripts that can be used to synchronize recordings:
* ```main_xdf``` is used to synchronize only two recordings from one session.
* ```main_xdf_batch``` can be used to automatize the synchronization of multiple sessions. To use ```main_xdf_batch```, you need an excel file in which the following information for each session is saved in the following columns:
    - session_ID
    - DBS ON/OFF
    - extracted mat files
    - LSL filename
    - sync side
    - IPG BIP
    - Synced
Adapt the paths corresponding to your own data structure, or copy or data structure based on the path described.


Expected datasets are .mat for intracerebral recordings and .xdf for external recordings. 
To obtain these formats:
* we stream our external datas from a TMSi SAGA data recorder sending samples to LSL, from which the output file is .xdf file
* we preprocess the .json files obtained after streaming from intracerebral DBS electrodes to obtain .mat files. To do so, we use the open source “Perceive” toolbox (https://github.com/neuromodulation/perceive) for MATLAB


## Getting Started

These instructions will get you a copy of the project up and running on your local machine. 

#### Repository
* GUI: use a git-manager of preference, and clone: https://github.com/juliettevivien/ReSyn_for_xdf.git
* Command line:
    - set working directory to desired folder and run: ```git clone https://github.com/juliettevivien/ReSync_for_xdf.git```
    - to check initiated remote-repo link, and current branch: ```cd ReSync_for_xdf```, ```git init```, ```git remote -v```, ```git branch``` (switch to branch main e.g. with git checkout main)

#### Environment
* Anaconda prompt: you can easily install the required environment from your Anaconda prompt:
    - navigate to repo directory, e.g.: ```cd Users/USERNAME/Research/ReSync```
    - ```conda env create –f environment.yml``` (Confirm Proceed? with ```y```)
    - ```conda activate resync_xdf```
    - ```git init```
 
* If for some reason this method is not working, try these lines in the Anaconda Prompt (it can happen for Mac users):
    - navigate to repo directory, e.g.: ```cd Users/USERNAME/Research/ReSync_for_xdf```
    - ```conda create --name resync_xdf python==3.10.9 pandas==1.5.3 scipy==1.10.0 numpy==1.23.5 openpyxl==3.0.10 jupyter==1.0.0```
    - ```conda activate resync_xdf```
    - ```pip install mne==1.3.0 pymatreader pybv mnelab```


## User Instructions:

* Make sure your environment has the required packages installed, either manually, or by following the instructions above.
* ReSync can be executed directly from the main.py or main_batch.py files.


## Authors

* **Juliette Vivien** - *Initial work* -

## Questions or contributions
Please don't hesitate to reach out if any questions or suggestions! @ juliette.vivien@charite.de  or https://twitter.com/vivien_juliette


## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details

