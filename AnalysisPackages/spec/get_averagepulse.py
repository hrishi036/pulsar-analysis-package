import sys
from pathlib import Path

import numpy as np

from os.path import isfile
from itertools import islice

from AnalysisPackages.utilities import utils
from AnalysisPackages.utilities.bcolors import bcolors
from AnalysisPackages.utilities.pulsar_information_utility import PulsarInformationUtility


# repeat
def ms_time_delay_to_time_quanta(t, psr):
    return t * ((psr.band[channel_number].sampling_frequency * 1000) / (512 * psr.n_packet_integration))


def main(file_name, ch_number, polarization):
    global channel_number
    global psr

    psr = PulsarInformationUtility(file_name)  # "B0834+06_20090725_114903"
    channel_number = int(ch_number[2:4])
    bins = int(round(ms_time_delay_to_time_quanta(psr.period, psr)))
    average_pulse_profile = create_nan_array(bins, psr.n_channels)
    specfile_chunk_size = 5000  # give proper name (this is chunk size)
    end_spec_file_flag = False
    root_dirname = str(Path(__file__).parent.parent.parent.absolute()) + '/'
    time_quanta_start = 0

    spec_file_path = utils.get_spec_file_name(root_dirname, psr, channel_number, polarization)
    if not isfile(spec_file_path):
        print(f"{bcolors.FAIL}file '{spec_file_path}' does not exist.\nExiting...{bcolors.ENDC}")
        exit()
    print(f"reading file {spec_file_path[112:]}")

    # read

    with open(spec_file_path, 'r') as spec_file:
        while not end_spec_file_flag:
            # read file
            dyn_spec, end_spec_file_flag = read_spec_file(end_spec_file_flag, specfile_chunk_size, spec_file)

            # get time series in mili seconds
            time_array, time_quanta_start = get_time_array(time_quanta_start, dyn_spec.shape[0])

            # remove rfi
            dyn_spec = utils.remove_rfi(dyn_spec, psr)

            # interpolate
            interpolated = interpolate_2D(dyn_spec, time_array, bins, psr)

            average_pulse_profile = np.nanmean(np.dstack((average_pulse_profile, interpolated)), axis=2)

            continue_flag = True if (input("continue folding?").lower() == "y") else False
            if not continue_flag:
                break
            if end_spec_file_flag:
                break

        utils.plot_DS(average_pulse_profile)
        output_filename = utils.get_average_pulse_file_name(root_dirname, psr, channel_number, polarization)
        np.savetxt(output_filename, average_pulse_profile)
        print("average pulse profile saved in file: ", output_filename)
        # return average_pulse_profile


def interpolate_2D(dyn_spec, time_array, bins, psr):
    interpolated_intermediate, interpolated_count = create_zero_array(bins, dyn_spec.shape[1]), \
                                                    create_zero_array(bins, dyn_spec.shape[1]),
    for i in range(time_array.shape[0]):
        f_p = (time_array[i] / psr.period) - int(time_array[i] / psr.period)
        n_bin = f_p * bins
        j = int(n_bin)
        if j == bins - 1:
            k = 0
        else:
            k = j + 1
        delta = n_bin - j

        if 0 <= j < bins - 1:
            for ch in range(psr.n_channels):
                if not np.isnan(dyn_spec[i, ch]):
                    interpolated_intermediate[j, ch] = interpolated_intermediate[j, ch] + dyn_spec[i, ch] * (1 - delta)
                    interpolated_intermediate[k, ch] = interpolated_intermediate[k, ch] + dyn_spec[i, ch] * delta
                    interpolated_count[j, ch] = interpolated_count[j, ch] + 1 - delta
                    interpolated_count[k, ch] = interpolated_count[k, ch] + delta
        # else:
        #
        #     print("else condition of 0 <= j < bins - 1: j value is ", j)

    return interpolated_intermediate / interpolated_count


def create_zero_array(rows, cols):
    return np.zeros((rows, cols))


def create_nan_array(rows, cols):
    a = np.zeros((rows, cols))
    a[:] = np.nan
    return a


def get_time_array(time_quanta_start, n_rows):
    time_array = utils.timequanta_to_millisec(np.arange(time_quanta_start, time_quanta_start + n_rows),
                                              psr, channel_number)
    time_quanta_start = time_quanta_start + n_rows
    return time_array, time_quanta_start


def read_spec_file(end_spec_file_flag, n_rows, spec_file):
    dyn_spec = np.genfromtxt(islice(spec_file, n_rows), dtype=float)
    print("spec file read. dyn_spec shape:", dyn_spec.shape)
    if dyn_spec.shape[0] < n_rows:
        print("eof for spec file reached")
        end_spec_file_flag = True

    return dyn_spec, end_spec_file_flag


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], sys.argv[3])  # B0834+06_20090725_114903 ch03 XX