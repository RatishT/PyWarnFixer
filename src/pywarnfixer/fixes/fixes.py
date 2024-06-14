import ast
import csv
import logging
import subprocess

from src.pywarnfixer.config import ENGAGEMENTS, STRATA_RANGES
from src.pywarnfixer.fixes.anthropic_api import anthropic_request
from src.pywarnfixer.fixes.context import Context
from src.pywarnfixer.fixes.pylint_fix import PylintFix

# Define the pylint fixes with appropriate context
PYLINT_FIXES = [
    PylintFix(name="no-else-return", code="R1705", context=Context.METHOD),
    PylintFix(name="unspecified-encoding", code="W1514", context=Context.METHOD),
    PylintFix(name="use-implicit-booleaness-not-comparison", code="C1803", context=Context.LINE),
    PylintFix(name="consider-using-with", code="R1732", context=Context.METHOD),
    PylintFix(name="unnecessary-comprehension", code="R1721", context=Context.LINE),
    PylintFix(name="consider-using-in", code="R1714", context=Context.LINE),
    PylintFix(name="chained-comparison", code="R1716", context=Context.LINE),
    PylintFix(name="useless-return", code="R1711", context=Context.METHOD),
    PylintFix(name="no-else-break", code="R1723", context=Context.METHOD),
    PylintFix(name="consider-using-ternary", code="R1706", context=Context.LINE)
]

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def auto_fix():
    """
    Main function to automatically fix pylint warnings for repositories.
    It fetches the repositories, parses pylint warnings, applies fixes, and runs tests.
    """
    logging.info("Fetching repositories...")
    for engagement in ENGAGEMENTS:
        for dataset_index, _ in enumerate(STRATA_RANGES, start=1):
            dataset_file_path = f"./datasets/{engagement}_{dataset_index}_projects.csv"
            repositories = fetch_repositories(dataset_file_path)

            for repo in repositories:
                creator, project_name = map(str.strip, repo.split('/'))
                repo_path = f'./repos/{engagement}_{dataset_index}/{creator}_{project_name}'
                warnings = parse_pylint_warnings(f'{repo_path}/pylint_output_w.txt')
                tests_passed = run_tests(repo_path)

                for warning in reversed(warnings):
                    for fix in PYLINT_FIXES:
                        if fix.code == warning['error_code']:
                            apply_fix_to_warning(fix, warning)
                            break

                if tests_passed:
                    assert run_tests(repo_path)


def fetch_repositories(dataset_file_path):
    """
    Fetches the list of repositories from the dataset file.

    Args:
        dataset_file_path (str): The path to the dataset file.

    Returns:
        list: A list of repository names.
    """
    repositories = []
    with open(dataset_file_path, 'r', encoding='utf8') as dataset_file:
        csv_reader = csv.reader(dataset_file)
        _ = next(csv_reader)
        for row in csv_reader:
            project_name = ''.join(row).strip()
            if project_name:
                repositories.append(project_name)
    return repositories


def parse_pylint_warnings(file_path):
    """
    Parses pylint warnings from a file into a structured format.

    Args:
        file_path (str): The path to the pylint output file.

    Returns:
        list: A list of dictionaries containing pylint warning details.
    """
    pylint_warnings = []
    with open(file_path, 'r', encoding='utf8') as file:
        for line in file:
            parts = line.strip().split(':')
            if len(parts) >= 5:
                try:
                    file_path, line_number, character, error_code, error_message = (
                        parts[0].strip(),
                        int(parts[1]),
                        parts[2].strip(),
                        parts[3].strip(),
                        parts[4].strip()
                    )
                    pylint_warnings.append({
                        'file_path': file_path,
                        'line_number': line_number,
                        'character': character,
                        'error_code': error_code,
                        'error_message': error_message
                    })
                except ValueError:
                    logging.warning(f"Skipping line due to parsing error: {line}")
    return pylint_warnings


def apply_fix_to_warning(fix, warning):
    """
    Applies the appropriate fix to a given pylint warning.

    Args:
        fix (PylintFix): The pylint fix to apply.
        warning (dict): The pylint warning details.
    """
    file_path = './' + warning['file_path'].replace('\\', '/')
    if check_python_file(file_path):
        code, line_start, line_end = extract_code_from_context(file_path, warning['line_number'],
                                                               fix.context)
        new_code = anthropic_request(warning['error_message'], code, fix.prompt)
        indented_new_code = add_indentation(new_code, get_starting_indentation(code))
        replace_code_in_file(file_path, indented_new_code, line_start, line_end)
        assert check_python_file(file_path)


def extract_code_from_context(file_path, line_number, context):
    """
    Extracts code from the file based on the given context (line, method, etc.).

    Args:
        file_path (str): The path to the file.
        line_number (int): The line number of the warning.
        context (Context): The context of the warning.

    Returns:
        tuple: Extracted code, starting line number, and ending line number.
    """
    match context:
        case Context.LINE:
            with open(file_path, 'r', encoding="utf8") as file:
                lines = file.readlines()
            return lines[line_number - 1], line_number, line_number
        case Context.METHOD:
            return extract_method_from_line(file_path, line_number)
        case _:
            logging.warning(f"Unsupported context {context} for line {line_number} in {file_path}")
            return '', 0, 0


def extract_method_from_line(file_path, line_number):
    """
    Extracts a method from the file based on the given line number.

    Args:
        file_path (str): The path to the file.
        line_number (int): The line number of the warning.

    Returns:
        tuple: Extracted method code, starting line number, and ending line number.
    """
    with open(file_path, 'r', encoding="utf8") as file:
        source = file.read()

    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            if node.lineno <= line_number <= node.end_lineno:
                method_lines = source.split('\n')[node.lineno - 1:node.end_lineno]
                method_str = '\n'.join(method_lines)
                return method_str, node.lineno, node.end_lineno

    logging.info(
        f"Method not found for line number {line_number} in {file_path}. Trying to extract line...")
    return extract_code_from_context(file_path, line_number, Context.LINE)


def replace_code_in_file(file_path, new_code, code_start, code_end):
    """
    Replaces code in the file from code_start to code_end with the new code.

    Args:
        file_path (str): The path to the file.
        new_code (str): The new code to insert.
        code_start (int): The starting line number of the code to replace.
        code_end (int): The ending line number of the code to replace.
    """
    with open(file_path, 'r', encoding="utf8") as file:
        lines = file.readlines()

    if code_start is not None and code_end is not None:
        del lines[code_start - 1:code_end]
        lines.insert(code_start - 1, new_code)
        with open(file_path, 'w', encoding="utf8") as file:
            file.writelines(lines)


def get_starting_indentation(code):
    """
    Gets the starting indentation level of the given code.

    Args:
        code (str): The code to analyze.

    Returns:
        int: The number of leading spaces in the first non-empty line.
    """
    for line in code.split('\n'):
        if line.strip():
            return len(line) - len(line.lstrip())
    return 0


def add_indentation(code, indentation):
    """
    Adds indentation to the given code.

    Args:
        code (str): The code to indent.
        indentation (int): The number of spaces to add.

    Returns:
        str: The indented code.
    """
    lines = code.split('\n')
    indented_lines = [(indentation * ' ' + line if line.strip() else line) for line in lines]
    return '\n'.join(indented_lines) + '\n'


def check_python_file(file_path):
    """
    Checks if the given Python file is syntactically correct.

    Args:
        file_path (str): The path to the file.

    Returns:
        bool: True if the file is syntactically correct, False otherwise.
    """
    try:
        with open(file_path, 'r', encoding="utf8") as file:
            script = file.read()
        compile(script, file_path, 'exec')
        logging.info(f"Python script {file_path} is syntactically correct.")
        return True
    except (SyntaxError, TypeError) as e:
        logging.error(f"Syntax error in {file_path}: {e}")
        return False
    except Exception as e:
        logging.error(f"Unexpected error in {file_path}: {e}")
        return False


def run_tests(repo_path):
    """
    Runs tests in the given repository path.

    Args:
        repo_path (str): The path to the repository.

    Returns:
        bool: True if tests passed, False otherwise.
    """
    try:
        result = subprocess.run(
            ['pytest'],
            cwd=repo_path,
            text=True,
            capture_output=True,
            check=True
        )
        logging.info(f"Tests passed for {repo_path}:\n{result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"Tests failed for {repo_path}:\n{e.stdout}\n{e.stderr}")
        return False
