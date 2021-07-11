"""
Old code... not refactored
todo : need to refactor this code
"""
import argparse
import warnings
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt

from AnalysisPackages.utilities import utils
from AnalysisPackages.utilities.pulsar_information_utility import PulsarInformationUtility


def calculate_dispersion_delay(ch, ref_ch, psr, channel_number):
    central_frequency = psr.band[channel_number].central_frequency
    band_width = psr.band[channel_number].sampling_frequency / 2
    ref_ch_freq_sq = np.square(central_frequency + (band_width / 2) - (ref_ch * band_width / (psr.n_channels - 1)))
    ch_freq_sq = np.square(central_frequency + (band_width / 2) - (ch * band_width / (psr.n_channels - 1)))

    t_delay = 4.15 * ((1 / ch_freq_sq) - (1 / ref_ch_freq_sq)) * np.power(10, 6) * psr.dm
    return utils.ms_time_delay_to_time_quanta(t_delay, channel_number, psr)


def main(file_name, ch_number, polarization):
    psr = PulsarInformationUtility(file_name)
    root_dirname = str(Path(__file__).parent.parent.parent.absolute()) + '/'
    ch_number = int(ch_number[2:4])
    psr_name = psr.psr_name_date_time

    plt.figure("average pulse profile " + psr_name + " " + str(ch_number) + " " + polarization)
    app = np.loadtxt(utils.get_average_pulse_file_name(root_dirname, psr, ch_number, polarization)).T
    utils.plot_DS(app.T)
    cent_freq = psr.get_central_frequency(ch_number)
    n_col = int(round(utils.ms_time_delay_to_time_quanta(psr.period, ch_number, psr)))

    ref_ch = int(input("Referance channel (Refer Figure): "))  # where center of pulse is seen
    pulse_start_bin = int(input("Pulse start col number (Refer Figure): "))
    pulse_end_bin = int(input("Pulse end col number (Refer Figure): "))  # where center of pulse is seen

    pulse_width = int((pulse_end_bin - pulse_start_bin) / 2) + 1
    print(pulse_width)
    ref_col = int((pulse_end_bin + pulse_start_bin) / 2)
    print(ref_col)
    mask = np.ones((psr.n_channels, n_col), dtype=float)
    print(app.shape)
    print(mask.shape)
    if ref_col - pulse_width < 0:
        mask[:, :ref_col + pulse_width] = np.nan
        mask[:, n_col - (pulse_width - ref_col):] = np.nan

    elif ref_col - pulse_width >= 0 and ref_col + pulse_width <= n_col:
        mask[:, ref_col - pulse_width: ref_col + pulse_width] = np.nan

    elif ref_col + pulse_width > n_col:
        mask[:, ref_col - pulse_width:] = np.nan
        mask[:, :ref_col + pulse_width - n_col] = np.nan

    for ch in range(psr.n_channels):
        col_delay = int(round(calculate_dispersion_delay(ch, ref_ch, psr, ch_number)))
        temp = np.array(np.roll(mask[ch, :], col_delay))
        mask[ch, :] = temp

    utils.plot_DS(mask.T)
    np.savetxt(utils.get_pulse_mask_filename(ch_number, root_dirname, polarization, psr), np.transpose(mask),
               fmt='%1.1f')

    masked_app = (app * mask).T
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=RuntimeWarning)
        average_spectrum = np.nanmean(masked_app, axis=0)
    plt.plot(average_spectrum)
    plt.show()
    np.savetxt(utils.get_average_spectrum_filename(ch_number, root_dirname, polarization, psr), average_spectrum,
               fmt='%1.1f')

    # print("Now Computing Spectrum Template")
    #
    # plt.figure("average pulse profile " + psr_name + " " + str(ch_number) + " " + polarization)
    # plt.imshow(app, interpolation="nearest")
    # plt.title("Note start and end column " + psr_name + " " + str(ch_number) + " " + polarization)
    # plt.show()
    #
    # col_start = int(input("Enter Starting Column (Refer Figure):"))
    # col_end = int(input("Enter End Column (Refer Figure):"))
    #
    # spec_template = np.mean(app[:, col_start:col_end],axis=1)
    # spec_template[spec_template == 0] = np.nan
    # plt.plot(spec_template)
    # plt.show()
    #
    # np.savetxt(get_avg_spectrum_template_filename(ch_number, root_dirname, polarization, psr), spec_template)
    quit()


def get_pulse_mask_filename(channel_number, root_dirname, polarization, psr):
    return root_dirname + f"OutputData/{psr.psr_name_date_time}/AveragePulseProfile/ch0{str(channel_number)}/" + \
           f"ch0{str(channel_number)}_{psr.psr_name_date_time}" + '_pulse_mask_' + polarization + ".prof"


def get_avg_spectrum_template_filename(channel_number, root_dirname, polarization, psr):
    return root_dirname + f"OutputData/{psr.psr_name_date_time}/AveragePulseProfile/ch0{str(channel_number)}/" + \
           f"ch0{str(channel_number)}_{psr.psr_name_date_time}" + '_avg_spectrum_' + polarization + ".prof"


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("input_file_name", type=str,
                        help="The mbr filename without the sequence number(eg. ch03_B0834+06_20090725_114903)")
    parser.add_argument("ch_number", type=str,
                        help="band number (eg. ch03 for band 3)")
    parser.add_argument("polarization", type=str,
                        help="polarization for which average pulse profile is to be obtained ('XX' or 'YY')")
    args = parser.parse_args()
    main(args.input_file_name, args.ch_number, args.polarization)  # B0834+06_20090725_114903 ch03 XX
