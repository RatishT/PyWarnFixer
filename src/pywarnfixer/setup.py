import requests
from pathlib import Path
import logging
from .config import GITHUB_ACCESS_TOKEN, ENGAGEMENTS, STRATA_RANGES, ORGANIZATION

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def setup_folders():
    """
    Create necessary folders for datasets, repositories,
    and reports based on engagement and strata ranges.
    """
    logging.info("Setting up folders...")
    Path('./datasets').mkdir(parents=True, exist_ok=True)

    for engagement in ENGAGEMENTS:
        for i, _ in enumerate(STRATA_RANGES, start=1):
            repo_folder = Path(f'./repos/{engagement}_{i}')
            report_folder = Path(f'./reports/{engagement}_{i}')

            repo_folder.mkdir(parents=True, exist_ok=True)
            report_folder.mkdir(parents=True, exist_ok=True)

    logging.info("Folders setup completed.")


def read_repo_list(file_path):
    """
    Read the repository list from the given file.

    Args:
        file_path (str): The path to the file containing repository names.

    Returns:
        list: A list of repository names.
    """
    logging.info(f"Reading repository list from {file_path}...")
    try:
        with open(file_path, 'r') as file:
            repo_list = [line.strip().split('/')[1] for line in file]
        logging.info(f"Successfully read {len(repo_list)} repositories.")
        return repo_list
    except FileNotFoundError:
        logging.error(f"File {file_path} not found.")
        return []


def delete_repo(repo_name):
    """
    Delete a repository from the organization on GitHub.

    Args:
        repo_name (str): The name of the repository to delete.
    """
    url = f"https://api.github.com/repos/{ORGANIZATION}/{repo_name}"
    headers = {'Authorization': f'token {GITHUB_ACCESS_TOKEN}'}

    try:
        response = requests.delete(url, headers=headers)

        if response.status_code == 204:
            logging.info(f"Repository {repo_name} deleted successfully.")
        else:
            logging.error(
                f"Failed to delete repository {repo_name}. Status code: {response.status_code}")
    except requests.RequestException as e:
        logging.error(f"An error occurred while deleting repository {repo_name}: {e}")


def delete_repos():
    """
    Delete repositories listed in files under the datasets directory.
    """
    logging.info("Starting repository deletion process...")
    for engagement in ENGAGEMENTS:
        for i in range(len(STRATA_RANGES)):
            repo_list_file = f"./datasets/{engagement}_{i + 1}_projects.txt"
            repo_list = read_repo_list(repo_list_file)

            for repo_name in repo_list:
                delete_repo(repo_name)

    logging.info("Repository deletion process completed.")
