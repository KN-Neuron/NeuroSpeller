import argparse
from data_reader import main as read_data
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
from consts import OUTPUT_DIR


def main(filename: str, plot_filter: bool, plot_fft: bool):
    print("\nReading data...")
    trials = read_data(filename)

    print("\nFiltering data...")
    filtered_epochs = filter_data(trials)

    for i, t in enumerate(trials):
        t.epoch = filtered_epochs[i]

    if plot_filter:
        print("\nGenerating filter plots...")
        plot_filter_time_domain(trials, filtered_epochs, filtered_epochs)
        plot_filter_psd_comparison(trials, filtered_epochs, filtered_epochs)

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
                    OUTPUT_DIR,
                )

        for ef in all_results:
            plot_grouped_fft(ef, all_results[ef], stats, OUTPUT_DIR)

        plot_snr_heatmap(stats, OUTPUT_DIR)

    print("\nPipeline complete!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the full SSVEP pipeline.")
    parser.add_argument("--filename", type=str, help="Path to the .mat file")
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
    args = parser.parse_args()

    main(args.filename, args.plot_filter, args.plot_fft)
