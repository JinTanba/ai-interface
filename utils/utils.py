from rich.console import Console
from rich.markdown import Markdown
from rich.syntax import Syntax
import re

def pprint(text: str | None) -> None:
    """
    Pretty-print text as Markdown or syntax-highlighted code depending
    on whether it is fenced with triple backticks.

    If the text starts and ends with ``` (optionally specifying a language,
    like ```python), it will be displayed as syntax-highlighted code;
    otherwise, it will be rendered as Markdown.
    """

    console = Console()

    # Return early if text is None
    if text is None:
        print('⚠️⚠️text is None')
        return text

    # Trim whitespace for easier detection
    stripped = text.strip()

    # Check if text is in triple backticks
    if stripped.startswith("```") and stripped.endswith("```"):
        # Split lines
        lines = stripped.split("\n")
        first_line = lines[0]   # e.g. ```python
        last_line  = lines[-1]  # should be ```

        # Default language
        lang = "python"

        # Attempt to detect language if specified in the first line
        # e.g. ```python or ```bash
        match = re.match(r"^```(\w+)$", first_line)
        if match:
            lang = match.group(1)

        # Get the code content between the triple backticks
        code_lines = lines[1:-1]
        code       = "\n".join(code_lines)

        # Create syntax object and print
        syntax = Syntax(code, lang, theme="monokai", line_numbers=True)
        print("⚠️ syntax detected")
        console.print(syntax)
    else:
        # Otherwise, treat as markdown
        print('markdown detected')
        md = Markdown(text)
        console.print(md)
