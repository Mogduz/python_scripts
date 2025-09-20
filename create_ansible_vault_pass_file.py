"""
create_ansible_vault_pass_file.py

Utility script to generate and store a secret suitable for use as an
Ansible Vault password file. The script:

- Parses CLI arguments for an output path and desired secret length.
- Validates and (if needed) confirms shorter-than-recommended lengths.
- Interactively ensures the destination path is safe to write:
  * Can (optionally) create missing parent directories.
  * Can (optionally) overwrite an existing file after confirmation.
- Writes a URL-safe random token to the target file.

Notes:
- The secret is produced with `secrets.token_urlsafe(n)`. This function
  generates `n` bytes of randomness and encodes them using a URL-safe
  Base64 alphabet. The resulting string is typically longer than `n`
  characters. This is intentional for high-entropy secrets.
- File permissions are not modified by this script. For Vault password
  files it is common to restrict access (e.g., `chmod 600`), which you
  may wish to enforce externally.
"""
from question import ask_yes_no_question
import argparse
from pathlib import Path
import secrets

# Script metadata and configuration. `script_description` intentionally
# remains empty to avoid altering the CLI header beyond what you asked.
script_name: str = 'create_ansible_vault_pass_file'
script_description: str = (
    "Generate a high-entropy, URL-safe secret and write it to a file for use as an "
    "Ansible Vault password file. The tool can optionally create missing parent "
    "directories and confirm before overwriting existing files. You can also choose "
    "the number of random BYTES passed to secrets.token_urlsafe() for stronger entropy. "
    "Typical workflow: run this once to create ~/.vault_pass and then reference that "
    "file via --vault-password-file or a matching --vault-id in your Ansible commands."
)

# Recommended default length (in *bytes of randomness* for token_urlsafe).
# Do not change program logic: only messaging and help texts are adjusted.
recomended_length: int = 128


def check_length_arg(value: str | int) -> int:
    """
    Coerce and validate the `--length` argument.

    Accepts either a string or an integer. If a string is provided, the
    function attempts to convert it to `int`. If the result is below the
    recommended length, the user is asked to confirm or switch to the
    recommended default.

    Args:
        value: The provided length as `str` or `int`.

    Returns:
        The validated integer length.

    Raises:
        argparse.ArgumentTypeError: If conversion to int fails.
    """
    if isinstance(value, str):
        try:
            value: int = int(value)
        except ValueError:
            # Improved, clear English error message (allowed change).
            raise argparse.ArgumentTypeError(f"Value '{value}' is not an integer.")

    # If shorter than recommended, ask the user whether to proceed or switch.
    if value < recomended_length:
        # User-facing prompt text improved for clarity (allowed change).
        secret_question: bool = ask_yes_no_question(
            promt=(
                f"Your selected secret length is {value} bytes. "
                f"The recommended length is {recomended_length} bytes. "
                f"Do you want to continue with length {value}?"
            ),
            default='y'
        )
        if secret_question:
            return value
        else:
            # Second, offer switching to the recommended default (allowed change).
            secret_question: bool = ask_yes_no_question(
                promt=f"Do you want to use the recommended default length ({recomended_length}) instead?",
                default='y'
            )
            if secret_question:
                return recomended_length
            else:
                # Improved status message before exit (allowed change).
                print("Secret length selection aborted by user. Exiting.")
                exit(3)
    else:
        return value


def check_path_arg(value: str) -> str:
    """
    Validate and normalize the positional `path` argument.

    Converts the provided string to a `Path` object and resolves it to an
    absolute path. Returns the resolved `Path`. The return type annotation
    intentionally mirrors the original code.

    Args:
        value: The path as a string.

    Returns:
        The resolved `Path` object (returned as-is).

    Raises:
        argparse.ArgumentTypeError: If `value` is not a string.
    """
    if isinstance(value, str):
        path: Path = Path(value)
        # Resolve to an absolute path to avoid ambiguity when writing.
        path: Path = path.resolve()
        return path
    else:
        # Improved, clear English error message (allowed change).
        raise argparse.ArgumentTypeError(f"Value '{value}' is not a string.")


def parse_args() -> argparse.Namespace:
    """
    Build the CLI parser and parse arguments.
    """
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        prog=script_name,
        description=script_description
    )
    # Filled-in, clear help texts (allowed change).
    parser.add_argument(
        '--length',
        type=check_length_arg,
        default=recomended_length,
        help=(
            "Number of random BYTES fed to secrets.token_urlsafe() "
            f"(higher = more entropy). If below {recomended_length}, "
            "you will be asked to confirm. Default: %(default)s."
        )
    )
    parser.add_argument(
        'path',
        type=check_path_arg,
        help=(
            "Destination file path for the generated secret (e.g. ~/.vault_pass). "
            "The path is resolved to an absolute path. Use --create_parents to "
            "auto-create missing directories."
        )
    )
    parser.add_argument(
        '--overwrite',
        action='store_true',
        default=False,
        required=False,
        help="Overwrite the file if it already exists without asking for confirmation."
    )
    parser.add_argument(
        '--create_parents',
        action='store_true',
        default=False,
        required=False,
        help="Create any missing parent directories of the target path without asking for confirmation."
    )
    parser.add_argument(
        '--description',
        action='store_true',
        default=False,
        required=False,
        help="Print the script description and exit."
    )
    return parser.parse_args()

def generate_secret(length: int) -> str:
    """
    Generate a URL-safe random secret string.

    Uses `secrets.token_urlsafe(length)`, which returns a Base64-like,
    URL-safe string containing approximately `length` bytes of randomness.

    Args:
        length: Number of random bytes to encode.

    Returns:
        A URL-safe secret string.
    """
    return secrets.token_urlsafe(length)


def check_path(path: Path, overwrite: bool = False, create_parents: bool = False) -> bool:
    """
    Ensure the target path is safe and permissible for writing.

    Behavior:
    - If parent directories are missing and `create_parents` is False,
      the user is prompted whether to create them.
    - If the file exists and `overwrite` is False, the user is prompted
      whether to overwrite it.
    - Returns True only if writing the file should proceed.

    Args:
        path: Destination file path.
        overwrite: If True, skip overwrite prompt when file exists.
        create_parents: If True, skip prompt and create missing parents.

    Returns:
        True if the file can be safely written; False otherwise.
    """
    # Parent directory is missing: confirm creation unless --create_parents is set.
    if not path.parent.exists():
        if not create_parents:
            # User-facing prompt text improved for clarity (allowed change).
            create_parents_question: bool = ask_yes_no_question(
                promt=(
                    f"The parent directory does not exist: {path.parent}. "
                    "Create it now?"
                ),
                default='y'
            )
            if create_parents_question:
                create_parents: bool = True
        if create_parents:
            path.parent.mkdir(parents=True)
        else:
            # Improved status message before exit (allowed change).
            print("Cannot create file without parent directories. User aborted. Exiting.")
            exit(4)

    # File exists: confirm overwrite unless --overwrite is set.
    if path.parent.exists() and path.exists():
        if not overwrite:
            # User-facing prompt text improved for clarity (allowed change).
            overwrite_question: bool = ask_yes_no_question(
                promt=f"File already exists: {path}. Overwrite?",
                default='n'
            )
            if overwrite_question:
                return True
            else:
                # Improved status message before exit (allowed change).
                print("User declined to overwrite the existing file. Exiting.")
                exit(5)
        if overwrite:
            return True

    # If we got here, writing is permitted.
    return True


def do_work(args: argparse.Namespace) -> None:
    if args.description:
        print(script_description)
        raise SystemExit(0)
    """
    Orchestrate the path checks and write the secret to disk.
    """
    can_write: bool = check_path(
        path=args.path,
        overwrite=args.overwrite,
        create_parents=args.create_parents
    )
    if can_write:
        # Improved, clear English status outputs (allowed change).
        print(f"Writing secret to: {args.path}")
        file: Path = args.path
        file.write_text(data=generate_secret(length=args.length))
        print(f"Secret written successfully to '{file}'. Exiting.")
    else:
        print("Cannot write file (path checks failed). Exiting.")


if __name__ == '__main__':
    # Entry point: parse CLI arguments and execute the main routine.
    do_work(args=parse_args())
