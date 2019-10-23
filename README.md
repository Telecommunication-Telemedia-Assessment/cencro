# cencro
A center cropped variant of Netflix's VMAF.


## Requirements
* build essentials (and requirements for vmaf)
* python >=3.6

To prepare the used vmaf tool run:
```
./prepare.sh
```

## Usage

```
usage: cencro.py [-h] [--tmp_folder_ref TMP_FOLDER_REF]
                 [--tmp_folder_dis TMP_FOLDER_DIS]
                 [--report_folder REPORT_FOLDER] [--pixel_format PIXEL_FORMAT]
                 [--height HEIGHT] [--width WIDTH] [--framerate FRAMERATE]
                 [--center_crops {-1,144,192,240,300,360,420,480,510,540,630,720,840,960,1020,1080,1260,1440,1800} [{-1,144,192,240,300,360,420,480,510,540,630,720,840,960,1020,1080,1260,1440,1800} ...]]
                 [--meta_from_ref] [--vmaf_model VMAF_MODEL]
                 reference_video distorted_video

run vmaf calculation, with yuv conversion and center croping parts

positional arguments:
  reference_video       reference video
  distorted_video       distorted video

optional arguments:
  -h, --help            show this help message and exit
  --tmp_folder_ref TMP_FOLDER_REF
                        tmp folder for storing converted reference videos
                        (default: ./yuv_r)
  --tmp_folder_dis TMP_FOLDER_DIS
                        tmp folder for storing converted distorted videos
                        (default: ./yuv_d)
  --report_folder REPORT_FOLDER
                        folder for storing reports; naming is based on
                        reference and distorted video (default: ./reports_cc)
  --pixel_format PIXEL_FORMAT
                        pixel_format (default: yuv422p10le)
  --height HEIGHT       height (default: 2160)
  --width WIDTH         width (default: 3840)
  --framerate FRAMERATE
                        framerate (default: 60)
  --center_crops {-1,144,192,240,300,360,420,480,510,540,630,720,840,960,1020,1080,1260,1440,1800} [{-1,144,192,240,300,360,420,480,510,540,630,720,840,960,1020,1080,1260,1440,1800} ...]
                        center crop (default: [360])
  --meta_from_ref       estimate framerate, height, width, pixel_format from
                        reference video (default: False)
  --vmaf_model VMAF_MODEL
                        used VMAF model (default: /home/sgoering/cencro/vmaf/m
                        odel/vmaf_rb_v0.6.3/vmaf_rb_v0.6.3.pkl)

stg7 2019
```

The simplest possible call is, assuming you have two videos, a reference `ref.mkv` and a distored `dis.mkv`,

```
./cencro.py ref.mkv dis.mkv --meta_from_ref
```

It will calculate 360 center cropped VMAF scores atfer pre-processing the distorted video to the same resolution, framerate and pixel format as the reference video.
A center crop of "-1" refers to a standard VMAF calculation without cropping, a so called uncropped VMAF.


## Reference
If you use `cencro` in your research please cite the following paper:

```
@inproceedings{goering2019cencro,
    author = {Steve G\"oring and Christopher Kr\"ammer and Alexander Raake},
    title = {cencro -- Speedup of Video Quality Calculation using Center Cropping},
    booktitle={2019 IEEE International Symposium on Multimedia (ISM)},
    year = {2019},
    pages={1-8},
    month={Dec}
}
```

## Acknowledgements

If you use this software in your research, please include a link to the repository and reference our paper.

## Licence
Except ffmpeg and other thirdparty software that have their own individual licences, the remaining software follows the:
GNU General Public License v3. See LICENSE file in this repository.
