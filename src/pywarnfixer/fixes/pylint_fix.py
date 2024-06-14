from src.pywarnfixer.fixes.context import Context

DEFAULT_PROMPT = (
    "Your task is to analyze the provided pylint warning and Python code snippet "
    "and provide a corrected version of the code that resolves the warning. "
    "The corrected code should be functional in a bigger context, efficient, and adhere to best practices in Python programming. "
    "Keep in mind that it is a snippet from a bigger script, therefore keep things such as indentation level and ending commas "
    "such that it still works in the broader context and don't add imports, packages, new classes or new functions. "
    "If a function or package is getting called, assume that it already exists and is imported. "
    "You can also assume that the code is syntactically correct and the only issue is the pylint warning. "
)


class PylintFix:
    """
    Represents a pylint fix with a name, code, context, and prompt.

    Attributes:
        name (str): The name of the pylint fix.
        code (str): The pylint warning code.
        prompt (str): The prompt used to generate a fix.
        context (Context): The context in which the fix is applied.
    """

    def __init__(self, name, code, prompt=DEFAULT_PROMPT, context=Context.METHOD):
        """
        Initializes a PylintFix instance.

        Args:
            name (str): The name of the pylint fix.
            code (str): The pylint warning code.
            prompt (str, optional): The prompt used to generate a fix. Defaults to DEFAULT_PROMPT.
            context (Context, optional): The context in which the fix is applied. Defaults to Context.METHOD.
        """
        self.name = name
        self.code = code
        self.prompt = prompt
        self.context = context

    def __str__(self):
        """
        Returns a string representation of the PylintFix instance.

        Returns:
            str: String representation of the PylintFix.
        """
        return f"PylintFix(name='{self.name}', code='{self.code}', prompt='{self.prompt}', context={self.context})"
