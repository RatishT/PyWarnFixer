import re
import logging
import anthropic

from src.pywarnfixer.config import ANTHROPIC_API_KEY

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def anthropic_request(pylint_warning, code, prompt):
    """
    Sends a request to the Anthropic API to analyze the given pylint warning and code.

    Args:
        pylint_warning (str): The pylint warning message.
        code (str): The code that caused the pylint warning.
        prompt (str): The system prompt for the API request.

    Returns:
        str: The response from the Anthropic API, either extracted code or the raw response.
    """
    logging.info("Creating Anthropic client.")
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    logging.info("Sending request to Anthropic API.")
    message = client.messages.create(
        model="claude-3-haiku-20240307",
        max_tokens=1000,
        temperature=0,
        system=prompt,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"{pylint_warning}\n{code}"
                    }
                ]
            }
        ]
    )

    logging.info("Received response from Anthropic API.")
    text = message.content[0].text

    # Regular expression pattern to match code between ```python and ```
    pattern = r"```python\s+(.*?)\s+```"

    logging.info("Extracting code from API response.")
    # Extract the code using regular expression
    match = re.search(pattern, text, re.DOTALL)
    if match:
        extracted_code = match.group(1)
        logging.info("Code extracted successfully.")
        return extracted_code
    else:
        logging.warning("No code block found in the response.")
        return text
