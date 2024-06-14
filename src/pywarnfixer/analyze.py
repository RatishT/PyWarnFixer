import csv
import math
import re
import logging
from collections import defaultdict
import matplotlib.pyplot as plt

from .config import ENGAGEMENTS, STRATA_RANGES, PYLINT_MESSAGE_TYPES, MAX_WARNINGS_PER_GRAPH

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def analyze():
    """
    Analyze all message types and generate reports.
    """
    for message_type in PYLINT_MESSAGE_TYPES:
        analyze_message_type(message_type)


def analyze_message_type(message_type):
    """
    Analyze a specific message type and generate density and ratio reports.

    Args:
        message_type: The type of pylint message to analyze.
    """
    densities = defaultdict(int)
    ratio = defaultdict(int)

    for engagement in ENGAGEMENTS:
        engagement_counts, engagement_ratios = analyze_engagement(engagement, message_type)
        for warning_tag, count in engagement_counts.items():
            densities[warning_tag] += count
        for warning_tag, count in engagement_ratios.items():
            ratio[warning_tag] += count

    densities = {k: v / len(ENGAGEMENTS) for k, v in densities.items()}
    ratio = {k: v / len(ENGAGEMENTS) for k, v in ratio.items()}
    save_and_plot("", densities, ratio, message_type)


def analyze_engagement(engagement, message_type):
    """
    Analyze a specific engagement for a given message type.

    Args:
        engagement: The type of engagement to analyze.
        message_type: The type of pylint message to analyze.

    Returns:
        Tuple of densities and ratios of warnings for the engagement.
    """
    engagement_densities = defaultdict(int)
    engagement_ratios = defaultdict(int)

    for stratum_idx in range(1, len(STRATA_RANGES) + 1):
        stratum_densities, stratum_ratios = analyze_stratum(engagement, stratum_idx, message_type)
        for warning_tag, count in stratum_densities.items():
            engagement_densities[warning_tag] += count
        for warning_tag, count in stratum_ratios.items():
            engagement_ratios[warning_tag] += count

    engagement_densities = {k: v / len(STRATA_RANGES) for k, v in engagement_densities.items()}
    engagement_ratios = {k: v / len(STRATA_RANGES) for k, v in engagement_ratios.items()}
    save_and_plot(f"{engagement}", engagement_densities, engagement_ratios, message_type)

    return engagement_densities, engagement_ratios


def analyze_stratum(engagement, stratum_idx, message_type):
    """
    Analyze a specific stratum for a given engagement and message type.

    Args:
        engagement: The type of engagement to analyze.
        stratum_idx: The index of the stratum to analyze.
        message_type: The type of pylint message to analyze.

    Returns:
        Tuple of densities and ratios of warnings for the stratum.
    """
    stratum_densities = defaultdict(int)
    stratum_ratios = defaultdict(int)

    projects = []
    stratum_file_path = f"./datasets/{engagement}_{stratum_idx}_project_sizes.csv"

    try:
        with open(stratum_file_path, 'r', encoding='utf-8-sig') as stratum_file:
            csv_reader = csv.reader(stratum_file)
            next(csv_reader)  # Skip header
            for row in csv_reader:
                project_name, size = row
                creator, project_name = map(str.strip, project_name.split('/'))
                try:
                    projects.append((f'{creator}_{project_name}', int(size)))
                except ValueError:
                    logging.warning(f'Invalid size for {project_name}.')
    except FileNotFoundError:
        logging.error(f'Stratum file {stratum_file_path} not found.')
        return {}, {}

    for project_name, size in projects:
        try:
            file_path = f'./reports/{engagement}_{stratum_idx}/{project_name}_warnings_{message_type}.csv'
            warning_counts = parse_pylint_file(file_path)
            for warning_tag, occurrences in warning_counts.items():
                stratum_densities[warning_tag] += math.ceil((occurrences / size) * 1000)
                stratum_ratios[warning_tag] += 1
        except FileNotFoundError:
            logging.warning(f'Warning counts for {project_name} not found.')

    num_projects = len(projects)
    stratum_densities = {k: v / num_projects for k, v in stratum_densities.items()}
    stratum_ratios = {k: v / num_projects for k, v in stratum_ratios.items()}
    save_and_plot(f"{engagement}_{stratum_idx}/{engagement}_{stratum_idx}", stratum_densities,
                  stratum_ratios, message_type)

    return stratum_densities, stratum_ratios


def parse_pylint_file(file_path):
    """
    Parse a pylint file to extract warning counts.

    Args:
        file_path: Path to the pylint file.

    Returns:
        A dictionary with warning tags and their counts.
    """
    warning_counts = {}

    try:
        with open(file_path, 'r') as file:
            csv_reader = csv.reader(file)
            next(csv_reader)  # Skip header
            for row in csv_reader:
                warning_counts[row[0]] = int(row[1])
    except FileNotFoundError:
        logging.error(f'Pylint file {file_path} not found.')

    return warning_counts


def save_and_plot(save_path, densities, ratios, message_type):
    """
    Save densities and ratios to CSV files and plot the warning counts.

    Args:
        save_path: The base path to save the files.
        densities: The densities of warnings.
        ratios: The ratios of warnings.
        message_type: The type of pylint message.
    """
    save_to_csv(f"./reports/{save_path}_densities_{message_type}.csv", densities, "Densities")
    plot_warning_counts(f"./reports/{save_path}_densities_{message_type}.png", densities,
                        ylabel="Densities")
    save_to_csv(f"./reports/{save_path}_ratios_{message_type}.csv", ratios, "Ratios")
    plot_warning_counts(f"./reports/{save_path}_ratios_{message_type}.png", ratios, ylabel="Ratios")


def save_to_csv(file_path, data, column_name):
    """
    Save data to a CSV file.

    Args:
        file_path: Path to the CSV file.
        data: Data to save.
        column_name: Column name for the data.
    """
    with open(file_path, 'w', newline='') as output_file:
        csv_writer = csv.writer(output_file)
        csv_writer.writerow(['warning_tag', column_name])
        csv_writer.writerows(data.items())


def plot_warning_counts(file_path, warning_counts, ylabel):
    """
    Plot warning counts and save as an image.

    Args:
        file_path: Path to save the image.
        warning_counts: Warning counts to plot.
        ylabel: Label for the y-axis.
    """
    # Sort the dictionary based on values (counts) in descending order
    top_warnings = {k: v for k, v in
                    sorted(warning_counts.items(), key=lambda item: item[1], reverse=True)[
                    :MAX_WARNINGS_PER_GRAPH]}

    warning_tags = list(top_warnings.keys())
    counts = list(top_warnings.values())

    # Create a bar plot
    plt.bar(warning_tags, counts)

    plt.xlabel('Warning Tags')
    plt.ylabel(ylabel)
    plt.title(f'Top {MAX_WARNINGS_PER_GRAPH} Warning Tag {ylabel}')
    plt.xticks(rotation=45, ha='right')  # Rotate x-axis labels for better readability
    plt.tight_layout()

    # Save the plot to a file
    plt.savefig(file_path)
    plt.clf()
