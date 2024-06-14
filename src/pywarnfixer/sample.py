import csv
import random
from time import sleep
from datetime import datetime, timedelta
from pathlib import Path

import requests
import logging

from .config import GITHUB_ACCESS_TOKEN, ENGAGEMENTS, STRATA_RANGES, MAX_PROJECTS_PER_STRATUM

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def sample_repositories():
    """
    Sample repositories for each stratum and save to files.
    """
    logging.info("Starting to sample repositories...")
    sampled_repos = {"oracle/oci-python-sdk"}

    for engagement in ENGAGEMENTS:
        for i, (start, end) in enumerate(STRATA_RANGES, start=1):
            stratum_filename = Path(f'./datasets/{engagement}_{i}_projects.csv')
            existing_repos = load_existing_repos(stratum_filename)
            sampled_repos.update(existing_repos)

            if len(existing_repos) >= MAX_PROJECTS_PER_STRATUM:
                continue

            new_repos = get_new_repositories(engagement, (start, end), sampled_repos)
            sampled_repos.update(new_repos)

            save_repositories_to_csv(stratum_filename, new_repos)

    logging.info("Finished sampling repositories.")


def load_existing_repos(file_path):
    """
    Load existing repositories from a CSV file.

    Args:
        file_path (Path): Path to the CSV file.

    Returns:
        list: List of existing repositories.
    """
    if file_path.exists():
        with file_path.open('r') as file:
            csv_reader = csv.reader(file)
            next(csv_reader)  # Skip header
            return [row[0] for row in csv_reader]
    return []


def get_new_repositories(engagement, engagement_range, sampled_repos):
    """
    Fetch new repositories based on engagement criteria and not already sampled.

    Args:
        engagement (str): Type of engagement (e.g., 'stars').
        engagement_range (tuple): Range of engagement values.
        sampled_repos (set): Set of already sampled repositories.

    Returns:
        list: List of new repositories.
    """
    new_repos = []

    for _ in range(MAX_PROJECTS_PER_STRATUM * 5):
        repos = fetch_repositories(engagement, engagement_range)
        unique_repos = set(repos) - sampled_repos
        new_repos.extend(unique_repos)
        sampled_repos.update(unique_repos)

        if len(new_repos) >= MAX_PROJECTS_PER_STRATUM:
            break

    return new_repos[:MAX_PROJECTS_PER_STRATUM]


def fetch_repositories(engagement, engagement_range):
    """
    Fetch repositories from GitHub based on engagement criteria.

    Args:
        engagement (str): Type of engagement (e.g., 'stars').
        engagement_range (tuple): Range of engagement values.

    Returns:
        list: List of repository full names.
    """
    start_date = (datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d')
    engagement_value = random.uniform(engagement_range[0], engagement_range[1])

    query = (f"{engagement}:{engagement_range[0]}..{engagement_value}"
             f" pushed:>={start_date} language:python")
    params = {
        'q': query,
        'sort': 'stars',
        'order': 'desc',
        'per_page': 1
    }
    headers = {'Authorization': f'token {GITHUB_ACCESS_TOKEN}'}

    try:
        response = requests.get('https://api.github.com/search/repositories', params=params,
                                headers=headers)
        response.raise_for_status()
        return [repo['full_name'] for repo in response.json().get('items', []) if
                has_merged_pr(repo['full_name'])]
    except requests.RequestException as e:
        logging.error(f"Failed to fetch repositories: {e}")
        sleep(60)
        return []


def has_merged_pr(full_name):
    """
    Check if a repository has a merged pull request in the past 6 months.

    Args:
        full_name (str): Full name of the repository (e.g., 'owner/repo').

    Returns:
        bool: True if the repository has a merged PR, False otherwise.
    """
    six_months_ago = (datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d')
    url = f'https://api.github.com/repos/{full_name}/pulls'
    params = {
        'state': 'closed',
        'sort': 'updated',
        'direction': 'desc',
        'per_page': 100,
    }
    headers = {'Authorization': f'token {GITHUB_ACCESS_TOKEN}'}

    try:
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        pulls = response.json()
        return any(pull.get('merged_at') and pull['merged_at'] >= six_months_ago for pull in pulls)
    except requests.RequestException as e:
        logging.error(f"Failed to fetch pull requests for {full_name}: {e}")
        return False


def save_repositories_to_csv(filename, repositories):
    """
    Save a list of repositories to a CSV file.

    Args:
        filename (Path): Path to the CSV file.
        repositories (list): List of repository full names.
    """
    with filename.open('w', newline='') as file:
        csv_writer = csv.writer(file)
        csv_writer.writerow(['project_name'])
        csv_writer.writerows([[repo] for repo in repositories])
        logging.info(f"Saved {len(repositories)} repositories to {filename}")
