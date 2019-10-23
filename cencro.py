#!/usr/bin/env python3
"""
    This file is part of cencro.
    cencro is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.
    cencro is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.
    You should have received a copy of the GNU General Public License
    along with cencro. If not, see <http://www.gnu.org/licenses/>.

    Author: Steve Göring
"""
import os
import sys
import shutil
import json
import argparse
import logging
import subprocess
import time

from core import *


VMAF_PATH = os.path.normpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), "./vmaf/src/libvmaf/vmafossexec"))
VMAF_MODEL = os.path.normpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), "./vmaf/model/vmaf_rb_v0.6.3/vmaf_rb_v0.6.3.pkl"))


def __run_multi_line_cmd(cmd):
    """
    run a command that consists of several lines that are combined again

    Parameters
    ----------
    cmd : str
        command to run, e.g. cmd="ls \n -la" will run "ls -la"

    TODO: move to utils/system?

    Returns
    -------
    in case of error an error is thrown

    Notes
    -----
    TODO: will be in future version not included in cencro
    """
    # remove multiple spaces in cmd
    cmd = " ".join(cmd.split())
    ret = os.system(cmd)
    if ret != 0:
        raise Exception(f"error in running command {cmd}")


def to_yuv(src, yuv_result, pixel_format, height, width, framerate, center_crop=-1):
    """
    converts a given video to a yuv version according to the given format,
    in case center_crop is not -1, it also performs a center cropping during conversion

    """
    if os.path.isfile(yuv_result):
        logging.info(f"{yuv_result} already converted")
        return
    logging.info(f"convert {src} to {yuv_result}")
    if center_crop > height:
        logging.error(f"center_crop {center_crop} <= video_height {height} must be ensured")
        sys.exit(0)
        return
    if center_crop == -1:
        cmd = f"""
        ffmpeg -nostdin -loglevel quiet -threads 4 -y -i "{src}"
            -vf scale={width}:{height},fps={framerate}
            -c:v rawvideo
            -framerate {framerate}
            -pix_fmt {pixel_format} "{yuv_result}" 2>/dev/null
        """
        __run_multi_line_cmd(cmd)
        return (width, height)

    center_crop_width = 2 * (int(center_crop * width / height) // 2)

    cmd = f"""
    ffmpeg -nostdin -loglevel quiet -threads 4
    -y
    -i {src}
    -filter:v scale={width}:{height},fps={framerate}
    -an
    -pix_fmt {pixel_format} -strict -1
    -f yuv4mpegpipe pipe:
    |
    ffmpeg -nostdin -loglevel quiet -threads 4
    -y -f yuv4mpegpipe
    -i pipe:
    -filter:v crop={center_crop_width}:{center_crop}
    -pix_fmt {pixel_format}
    -framerate {framerate}
    -c:v rawvideo
    -an
    {yuv_result} 2>/dev/null"""

    __run_multi_line_cmd(cmd)
    return


def make_directories(dirs):
    for d in dirs:
        os.makedirs(d, exist_ok=True)

def run_vmaf(ref, dis, tmp_folder_ref, tmp_folder_dis, report_folder, pixel_format="yuv422p10le", height=2160, width=3840, framerate=60, vmaf_model="vmaf_4k_v0.6.1.pkl", delete_yuv_ref=True, center_crop=-1):
    """
    calculates vmaf scores for a given red and dis video; performs center cropping
    """
    make_directories([tmp_folder_ref, tmp_folder_dis, report_folder])

    cc_str = "_{center_crop}".format(center_crop=center_crop)
    yuv_ref = os.path.join(tmp_folder_ref, flat_name(get_basename(ref)) + "_" + flat_name(get_basename(os.path.basename(dis))) + cc_str + ".yuv")
    yuv_dis = os.path.join(tmp_folder_dis, flat_name(get_basename(dis)) + cc_str + ".yuv")

    report_name = os.path.join(report_folder, flat_name(get_basename(dis)) + cc_str + ".json")

    if os.path.isfile(report_name):
        logging.info(f"{report_name} already calculated")
        return
    logging.info(f"convert to yuv {ref}, {dis}")

    start_time = time.time()
    to_yuv(ref, yuv_ref, pixel_format, height, width, framerate, center_crop)
    ref_conversion_time = time.time() - start_time

    start_time = time.time()
    to_yuv(dis, yuv_dis, pixel_format, height, width, framerate, center_crop)
    dis_conversion_time = time.time() - start_time
    yuv_width = width
    yuv_height = height
    if center_crop != -1:
        yuv_width = 2 * (int(center_crop * width / height) // 2)
        yuv_height = center_crop

    logging.info(f"calculate vamf {ref}, {dis}")

    vmaf_cmd = f"""
    {VMAF_PATH} {pixel_format} {yuv_width} {yuv_height} {yuv_ref} {yuv_dis} {VMAF_MODEL} --log {report_name} --log-fmt json --thread 0 --psnr --ssim --ci
    """
    start_time = time.time()
    os.system(vmaf_cmd)
    vmaf_run_time = time.time() - start_time
    # only delete distorted video yuv file, however reference video is maybe used somewhere else
    os.remove(yuv_dis)
    if delete_yuv_ref:
        os.remove(yuv_ref)

    logging.info("timings: {}".format(json.dumps({
            "ref_conversion_time": ref_conversion_time,
            "dis_conversion_time": dis_conversion_time,
            "vmaf_run_time": vmaf_run_time,
            "crop": center_crop,
            "dis_video": dis
    })))

    logging.info(f"vmaf calculation done for {ref}, {dis}")
    return report_name



def main(_):
    center_crops = [-1, 144, 192, 240, 300, 360, 420, 480, 510, 540, 630, 720, 840, 960, 1020, 1080, 1260, 1440, 1800]
    # argument parsing
    parser = argparse.ArgumentParser(description='run vmaf calculation, with yuv conversion and center croping parts',
                                     epilog="stg7 2019",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("reference_video", type=str, help="reference video")
    parser.add_argument("distorted_video", type=str, help="distorted video")
    parser.add_argument("--tmp_folder_ref", type=str, default="./yuv_r", help="tmp folder for storing converted reference videos")
    parser.add_argument("--tmp_folder_dis", type=str, default="./yuv_d", help="tmp folder for storing converted distorted videos")
    parser.add_argument("--report_folder", type=str, default="./reports_cc", help="folder for storing reports; naming is based on reference and distorted video")
    parser.add_argument("--pixel_format", type=str, default="yuv422p10le", help="pixel_format")
    parser.add_argument("--height", type=int, default=2160, help="height")
    parser.add_argument("--width", type=int, default=3840, help="width")
    parser.add_argument("--framerate", type=int, default=60, help="framerate")
    parser.add_argument("--center_crops", type=int, nargs='+', default=[360], choices=center_crops, help="center crop")

    parser.add_argument("--meta_from_ref", action='store_true', help="estimate framerate, height, width, pixel_format from reference video")
    parser.add_argument("--vmaf_model", type=str, default=VMAF_MODEL, help="used VMAF model")

    logging.basicConfig(level=logging.DEBUG)
    logging.info("calculate vmaf scores")

    a = vars(parser.parse_args())
    logging.info(f"params: {json.dumps(a, indent=4)}")

    assert_file(VMAF_PATH, "you need to have a compiled vmaf running, so run ./prepare.sh and check errors")
    assert_file(a["reference_video"], f"""reference video {a["reference_video"]} does not exist""")
    assert_file(a["distorted_video"], f"""distorted video {a["distorted_video"]} does not exist""")

    if a["meta_from_ref"]:
        meta = ffprobe(a["reference_video"])
        logging.info("estimated meta data: \n {}".format(json.dumps(meta, indent=4, sort_keys=True)))
        a["height"] = meta["height"]
        a["framerate"] = meta["avg_frame_rate"]
        a["pixel_format"] = meta["pix_fmt"]

    if a["center_crops"] is None:
        a["center_crops"] = center_crops

    for center_crop in a["center_crops"]:
        logging.info(f"handle center crop {center_crop}")
        run_vmaf(
            a["reference_video"],
            a["distorted_video"],
            a["tmp_folder_ref"],
            a["tmp_folder_dis"],
            a["report_folder"],
            a["pixel_format"],
            a["height"],
            a["width"],
            a["framerate"],
            a["vmaf_model"],
            center_crop=center_crop
        )


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
