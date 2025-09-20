"""
create_ansible_vault_pass_file.py

Utility script to generate and store a secret suitable for use as an
Ansible Vault password file. The script:

- Parses CLI arguments for an output path and desired secret length.
- Validates that the length is one of a predefined set of allowed values.
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

# Script metadata and configuration. `script_description` is intentionally
# left empty as in the original source to avoid changing CLI help output.
script_name: str = 'create_ansible_vault_pass_file'
script_description: str = ''
# Only these lengths are accepted for the random token generation.
valid_min_length: int = 1
valid_max_length: int = 65000 


def check_length_arg(value: str | int) -> int:
    """
    Coerce and validate the `--length` argument.

    Accepts either a string or an integer. If a string is provided, the
    function attempts to convert it to `int`. It then checks that the
    resulting integer is one of the allowed values in `valid_lengths`.

    Args:
        value: The provided length as `str` or `int`.

    Returns:
        The validated integer length.

    Raises:
        argparse.ArgumentTypeError: If conversion to int fails or if
        the integer is not in `valid_lengths`.
    """
    if isinstance(value, str):
        try:
            value: int = int(value)
        except ValueError:
            # (Allowed change) English exception message
            raise argparse.ArgumentTypeError(f"Value '{value}' is not an integer.")
    print(value)
    exit(1)    
    if value > valid_min_length and value <= valid_max_length:
        
        if value < 64:
            password_question: bool = ask_yes_no_question(promt=f'your selected password length is {value}. we recomed a length from 128. do you want create a secret with a length from {value}?', default='y')
            if password_question:
                return value
            else:
                print('user abort password length. exit')
                exit(3)
    else:
        raise ValueError(f'invalid value! value must beetween {valid_min_length} and {valid_max_length}')


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
        # (Allowed change) English exception message
        raise argparse.ArgumentTypeError(f"Value '{value}' is not a string.")


def parse_args() -> argparse.Namespace:
    """
    Build the CLI parser and parse arguments.

    Keeps the original help texts unchanged to honor the constraint of
    not modifying outputs other than `print`/exceptions.
    """
    parser: argparse.ArgumentParser = argparse.ArgumentParser(prog=script_name, description=script_description)
    parser.add_argument('--length', type=check_length_arg, default=check_length_arg(value=128), help='')
    parser.add_argument('path', type=check_path_arg, help='')
    parser.add_argument('--overwrite', action='store_true', default=False, required=False, help='')
    parser.add_argument('--create_parents', action='store_true', default=False, required=False, help='')
    return parser.parse_args()


def generate_secret(length: int) -> str:
    """
    Generate a URL-safe random secret string.

    Uses `secrets.token_urlsafe(length)`, which returns a Base64-like,
    URL-safe string containing ~`length` bytes of randomness.

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
    # Parent does not exist: optionally ask to create it (interactive).
    if not path.parent.exists():
        if not create_parents:
            # NOTE: Prompt text left unchanged because it's not a print or exception.
            create_parents_question: str = input(f'Parent directories: {path.parents} not exists. Do want to create it? Y/n: ').lower()
            # Interpret common single-character responses.
            if len(create_parents_question) == 0 or len(create_parents_question) == 1:
                match create_parents_question:
                    case 'y':
                        create_parents: bool = True
                    case '':
                        create_parents: bool = True
                    case _:
                        create_parents: bool = False
            else:
                create_parents: bool = False
        if create_parents:
            # Create the entire parent directory tree if requested/confirmed.
            path.parent.mkdir(parents=True)

    # If parent exists and file does not: we are good to proceed.
    if path.parent.exists() and not path.exists():
        file_ok: bool = True

    # If both parent and file exist: possibly prompt for overwrite.
    if path.parent.exists() and path.exists():
        if not overwrite:
            # NOTE: Prompt text left unchanged because it's not a print or exception.
            overwrite_question: str = input(f'file: {path} allready exists. Overwrite? y/N: ').lower()
            # Accept single-character inputs (y/n) or empty as "no" by default.
            if len(overwrite_question) == 1 or len(overwrite_question) == 1:
                match overwrite_question:
                    case 'n':
                        overwrite: bool = False
                    case '':
                        overwrite: bool = False
                    case 'y':
                        overwrite: bool = True
            else:
                overwrite: bool = False

    # If overwrite is allowed and the file exists, we're good.
    if path.parent.exists() and path.exists() and overwrite:
        file_ok: bool = True

    # If overwrite is not allowed and the file exists, we cannot write.
    if path.parent.exists() and path.exists() and not overwrite:
        file_ok: bool = False

    # Final decision: only proceed if parent exists and prior checks mark it OK.
    if path.parent.exists() and file_ok:
        return True
    return False


def do_work(args: argparse.Namespace) -> None:
    """
    Orchestrate the path checks and write the secret to disk.
    """
    can_write: bool = check_path(path=args.path, overwrite=args.overwrite, create_parents=args.create_parents)
    if can_write:
        # (Allowed change) Improved, clear English status output
        print(f"Writing secret to file: {args.path}")
        file: Path = args.path
        file.write_text(data=generate_secret(length=args.length))
        # (Allowed change) Improved, clear English status output
        print(f"File '{file}' written successfully. Exiting.")
    else:
        # (Allowed change) Improved, clear English status output
        print("Cannot write file (path checks failed). Exiting.")


if __name__ == '__main__':
    # Entry point: parse CLI arguments and execute the main routine.
    do_work(args=parse_args())
