import argparse
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt

from AnalysisPackages.utilities import utils
from AnalysisPackages.utilities.pulsar_information_utility import PulsarInformationUtility


def main(file_name, ch_number, polarization, bins: int):
    psr = PulsarInformationUtility(file_name)  # "B0834+06_20090725_114903"
    channel_number = int(ch_number[2:4])
    root_dirname = str(Path(__file__).parent.parent.parent.absolute()) + '/'

    with open(utils.get_time_series_filename(channel_number, root_dirname, polarization, psr), 'r') as time_series_file:
        time_series = np.loadtxt(time_series_file)
    total_periods = int(time_series[-1, 0] / psr.period) + 1

    interpolated_intermediate, interpolated_count = np.zeros(bins * total_periods, dtype="float"), \
                                                    np.zeros(bins * total_periods, dtype="float")
    for time_series_quanta in time_series:
        n_bin = (time_series_quanta[0] / psr.period) * bins
        j = int(n_bin)
        if j == bins - 1:
            k = 0
        else:
            k = j + 1
        delta = n_bin - j

        if 0 <= j < bins * total_periods - 1:
            if not np.isnan(time_series_quanta[1]):
                interpolated_intermediate[j] = interpolated_intermediate[j] + time_series_quanta[1] * (1 - delta)
                interpolated_intermediate[k] = interpolated_intermediate[k] + time_series_quanta[1] * delta
                interpolated_count[j] = interpolated_count[j] + 1 - delta
                interpolated_count[k] = interpolated_count[k] + delta
        else:
            print("else condition of 0 <= j < bins - 1: j value is ", j)

    binned_time_series = np.divide(interpolated_intermediate, interpolated_count,
                                   out=np.zeros_like(interpolated_intermediate), where= interpolated_count!=0)
    binned_time_series_filename = utils.get_binned_time_series_filename(channel_number, root_dirname, polarization, psr)
    pulse_stack_filename = utils.get_pulse_stack_filename(channel_number, root_dirname, polarization, psr)
    np.savetxt(binned_time_series_filename, binned_time_series)
    print(f"saved binned time series to: ", binned_time_series_filename)
    np.savetxt(pulse_stack_filename, binned_time_series.reshape(-1, bins))
    print(f"saved pulse stack to: ", pulse_stack_filename)
    integrated_filename = utils.get_integrated_pulse_stack_filename(channel_number, root_dirname, polarization, psr)
    np.savetxt(integrated_filename, np.sum(binned_time_series.reshape(-1, bins), axis=0))
    print(f"saved integrated pulse stack to: ", pulse_stack_filename)

    # plt.plot(binned_time_series)
    # plt.show()
    # pulsestack = binned_time_series.reshape(-1, bins)
    # plt.imshow(pulsestack.reshape(-1, bins), extent=[0, 1, 0, pulsestack.shape[0]], origin="lower", aspect=1/2000)
    # plt.xlabel("Longitude")
    # plt.ylabel("Period")
    # plt.show()
    # plt.plot(np.linspace(0, 0.999, 1000), np.sum(binned_time_series.reshape(-1, bins), axis=0))
    # plt.xlim(0,1)
    # plt.ylim(-32, 130)
    # plt.title("Decompression By Both Methods - B0809+74 Band 01")
    # plt.xlabel("Longitude")
    # plt.show()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("file_name", type=str,
                        help="The mbr filename without the sequence number(eg. ch03_B0834+06_20090725_114903)")
    parser.add_argument("ch_number", type=str,
                        help="band number (eg. ch03 for band 3)")
    parser.add_argument("polarization", type=str,
                        help="polarization for which average pulse profile is to be obtained "
                             "('XX', 'YY' or 'I' for stokes I)")
    parser.add_argument("-b", "--bins", type=int, default=1000, metavar="<int>",
                        help="number of bins in one period (default value is 1000)")

    args = parser.parse_args()
    main(args.file_name, args.ch_number, args.polarization, args.bins) # B0834+06_20090725_114903 ch03 XX 1000
