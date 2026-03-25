import argparse
from data_reader import DataReader, MatDataReader
from filter import main as filter_data
from fft_analysis import main as fft_analysis_main
from filter_plotter import (
    plot_time_domain as plot_filter_time_domain,
    plot_psd_comparison as plot_filter_psd_comparison,
)
from fft_plotter import (
    plot_snr_heatmap,
    plot_grouped_fft,
    plot_single_trial_fft,
)
from consts import OUTPUT_DIR, DATA_READERS
import numpy as np


def main(
    filename: str,
    plot_filter: bool,
    plot_fft: bool,
    reader: DataReader,
    output_dir: str = OUTPUT_DIR,
):
    print("\nReading data...")
    trials = reader.get_all_trials(filename)

    # Save raw (unfiltered) epochs before applying any filtering
    raw_epochs = np.array([t.epoch for t in trials])

    print("\nFiltering data...")
    filtered_epochs = filter_data(trials)

    for i, t in enumerate(trials):
        t.epoch = filtered_epochs[i]

    if plot_filter:
        print("\nGenerating filter plots...")
        plot_filter_time_domain(trials, raw_epochs, filtered_epochs)
        plot_filter_psd_comparison(trials, raw_epochs, filtered_epochs)

    print("\nPerforming FFT and SNR analysis...")
    fft_results = fft_analysis_main(trials)

    if plot_fft:
        print("\nGenerating FFT plots...")
        all_results = fft_results["all_results"]
        stats = fft_results["stats"]

        for ef in all_results:
            for r in all_results[ef]:
                trial = next(t for t in trials if t.trial == r["trial"])
                plot_single_trial_fft(
                    trial,
                    r["magnitude"],
                    r["ch_idx"],
                    r["channel"],
                    r["snr_db"],
                    output_dir,
                )

        for ef in all_results:
            plot_grouped_fft(ef, all_results[ef], stats, output_dir)

        plot_snr_heatmap(stats, output_dir)

    print("\nPipeline complete!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the full SSVEP pipeline.")
    parser.add_argument("--filename", type=str, help="Path to the data file")
    parser.add_argument("--data_type", type=str, help="csv or mat")
    parser.add_argument(
        "--plot_filter",
        action="store_true",
        help="Generate plots for the filtered signal (time-domain and PSD)",
    )
    parser.add_argument(
        "--plot_fft",
        action="store_true",
        help="Generate plots for the FFT results (SNR heatmap, FFT spectrum)",
    )
    parser.add_argument("--output", type=str, help="output directory")
    args = parser.parse_args()

    reader_class = DATA_READERS.get(args.data_type)

    main(args.filename, args.plot_filter, args.plot_fft, reader_class(), args.output)
