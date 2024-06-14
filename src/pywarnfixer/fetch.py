import csv
import subprocess
import re
from collections import defaultdict
from time import sleep
from pathlib import Path
import logging
import requests

from .config import GITHUB_ACCESS_TOKEN, ENGAGEMENTS, STRATA_RANGES, PYLINT_MESSAGE_TYPES, \
    ORGANIZATION

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def fetch_repositories():
    """
    Fetch repositories, analyze them, and save the results.
    """
    logging.info("Fetching repositories...")
    for engagement in ENGAGEMENTS:
        for dataset_idx, _ in enumerate(STRATA_RANGES, start=1):
            dataset_file_path = Path(f"./datasets/{engagement}_{dataset_idx}_projects.csv")
            repositories = read_dataset_file(dataset_file_path)

            for project in repositories:
                creator, project_name = map(str.strip, project.split('/'))
                analyze_repository(engagement, dataset_idx, creator, project_name)
                size = get_repository_size(
                    Path(f"./repos/{engagement}_{dataset_idx}/{creator}_{project_name}"))
                repositories.append([project, size])

            save_repositories_to_csv(
                Path(f"./datasets/{engagement}_{dataset_idx}_project_sizes.csv"), repositories)


def read_dataset_file(file_path):
    """
    Read CSV file with GitHub repositories.

    Args:
        file_path (Path): Path to the CSV file.

    Returns:
        list: List of repositories.
    """
    with file_path.open('r', encoding='utf8') as dataset_file:
        csv_reader = csv.reader(dataset_file)
        next(csv_reader)  # Skip header
        return [row[0] for row in csv_reader]


def analyze_repository(engagement, dataset_idx, creator, project_name):
    """
    Analyze a single repository, including forking, cloning, running Pylint, and saving warning counts.

    Args:
        engagement (str): Type of engagement (e.g., 'stars').
        dataset_idx (int): Index of the dataset.
        creator (str): Creator of the repository.
        project_name (str): Name of the repository.
    """
    repo_directory = Path(f"./repos/{engagement}_{dataset_idx}/{creator}_{project_name}")

    if repo_directory.exists():
        logging.info(f"Repository {creator}/{project_name} already cloned.")
    else:
        repo_url = f"https://api.github.com/repos/{creator}/{project_name}"
        response = requests.get(repo_url)

        if response.status_code == 200:
            logging.info(f"Forking {creator}/{project_name}...")
            forked_clone_url = fork_repository(repo_url)

            if forked_clone_url:
                clone_repository(forked_clone_url, repo_directory)
        else:
            logging.error(
                f"Failed to fetch data for {creator}/{project_name}. Status code: {response.status_code}")
            return

    run_pylint(repo_directory, creator, project_name)
    parse_pylint_output(engagement, dataset_idx, creator, project_name, repo_directory)


def fork_repository(repo_url):
    """
    Fork the repository using the GitHub API.

    Args:
        repo_url (str): URL of the repository to fork.

    Returns:
        str: Clone URL of the forked repository, or None if the fork failed.
    """
    fork_url = f"{repo_url}/forks?organization={ORGANIZATION}"
    headers = {'Authorization': f'token {GITHUB_ACCESS_TOKEN}'}
    response = requests.post(fork_url, headers=headers)

    if response.status_code == 202:  # Accepted (forking is in progress)
        logging.info("Forking repository...")
        return response.json().get('clone_url')
    else:
        logging.error(f"Failed to fork repository. Status code: {response.status_code}")
        return None


def clone_repository(repo_url, repo_directory):
    """
    Clone the repository, retrying up to 5 times.

    Args:
        repo_url (str): URL of the repository to clone.
        repo_directory (Path): Directory to clone the repository into.
    """
    for i in range(5):
        if is_repo_ready(repo_url):
            subprocess.run(["git", "clone", repo_url, str(repo_directory)])
            logging.info(f"Repository cloned successfully: {repo_directory}")
            break
        else:
            sleep(5)
    else:
        logging.error(f"Could not clone repository: forked repository {repo_url} not found.")


def is_repo_ready(repo_url):
    """
    Check if the repository is ready (status code 200).

    Args:
        repo_url (str): URL of the repository.

    Returns:
        bool: True if the repository is ready, False otherwise.
    """
    response = requests.get(repo_url)
    return response.status_code == 200


def run_pylint(directory, creator, project_name):
    """
    Run Pylint on the repository for different message types.

    Args:
        directory (Path): Directory of the repository.
        creator (str): Creator of the repository.
        project_name (str): Name of the repository.
    """
    for message_type in PYLINT_MESSAGE_TYPES:
        pylint_output_path = directory / f"pylint_output_{message_type}.txt"
        if pylint_output_path.exists():
            logging.info(f"Warnings ({message_type}) for {creator}/{project_name} already exist.")
        else:
            run_pylint_message(directory, pylint_output_path, message_type)


def run_pylint_message(directory, pylint_output_path, message_type):
    """
    Run Pylint for a specific message type and save the output to a file.

    Args:
        directory (Path): Directory of the repository.
        pylint_output_path (Path): Path to save the Pylint output.
        message_type (str): Pylint message type to enable.
    """
    logging.info(f"Analyzing {directory} for {message_type} messages...")

    with pylint_output_path.open('w') as output_file:
        if message_type == "ALL":
            subprocess.run(["pylint", "--recursive=y", str(directory)], stdout=output_file)
        else:
            subprocess.run(["pylint", "--disable=all", f"--enable={message_type}", "--recursive=y",
                            str(directory)], stdout=output_file)


def parse_pylint_output(engagement, dataset_idx, creator, project_name, directory):
    """
    Parse Pylint output files and save the results.

    Args:
        engagement (str): Type of engagement (e.g., 'stars').
        dataset_idx (int): Index of the dataset.
        creator (str): Creator of the repository.
        project_name (str): Name of the repository.
        directory (Path): Directory of the repository.
    """
    for message_type in PYLINT_MESSAGE_TYPES:
        pylint_output_path = directory / f"pylint_output_{message_type}.txt"
        parsed_warning_path = Path(
            f"./reports/{engagement}_{dataset_idx}/{creator}_{project_name}_warnings_{message_type}.csv")
        if parsed_warning_path.exists():
            logging.info(
                f"Parsed warnings ({message_type}) for {creator}/{project_name} already exist.")
        else:
            parse_pylint_output_message(pylint_output_path, parsed_warning_path)


def parse_pylint_output_message(pylint_output_path, parsed_warning_path):
    """
    Parse a Pylint output file and save the warnings to a CSV file.

    Args:
        pylint_output_path (Path): Path to the Pylint output file.
        parsed_warning_path (Path): Path to save the parsed warnings.
    """
    with pylint_output_path.open('r', encoding="utf8") as file:
        pylint_output = file.read()

    warning_pattern = re.compile(r"^(.+):[0-9]+:[0-9]+: (\S+): (.+) \((.+)\)$", re.MULTILINE)
    matches = warning_pattern.findall(pylint_output)

    warnings = defaultdict(int)
    for match in matches:
        warning_tag = match[3]
        warnings[warning_tag] += 1

    with parsed_warning_path.open('w', newline='') as output_file:
        csv_writer = csv.writer(output_file)
        csv_writer.writerow(["Warning Tag", "Count"])
        csv_writer.writerows(warnings.items())

    for warning_tag, count in warnings.items():
        logging.info(f"{warning_tag}: {count} occurrences")


def get_repository_size(directory):
    """
    Get the size of the repository.

    Args:
        directory (Path): Directory of the repository.

    Returns:
        str: Size of the repository.
    """
    logging.info(f"Calculating size of {directory}...")
    command = f'powershell.exe -Command "Get-ChildItem -Path {directory} -Filter *.py -Recurse | ForEach-Object {{ Get-Content $_.FullName | Measure-Object -Line }} | Measure-Object -Property Lines -Sum | Select-Object -ExpandProperty Sum"'
    result = subprocess.run(command, capture_output=True, text=True, shell=True)
    size = result.stdout.strip()
    logging.info(f"Size of the repository: {size}")
    return size


def save_repositories_to_csv(filename, repositories):
    """
    Save a list of repositories and their sizes to a CSV file.

    Args:
        filename (Path): Path to the CSV file.
        repositories (list): List of repositories and their sizes.
    """
    with filename.open('w', newline='') as file:
        csv_writer = csv.writer(file)
        csv_writer.writerow(['project_name', 'size'])
        csv_writer.writerows(repositories)
        logging.info(f"Saved {len(repositories)} repositories to {filename}")
