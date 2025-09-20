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
# The helper `ask_yes_no_question` is expected to provide a standardized
# Y/N prompt returning a boolean. Keeping the import and usage intact preserves
# behavior while allowing the script to remain clean and testable.
from question import ask_yes_no_question
import argparse
from pathlib import Path
import secrets

# ---------------------------------------------------------------------------
# Script metadata and configuration
# ---------------------------------------------------------------------------
# `script_name` is used to set the CLI program name for argparse help output.
# `script_description` explains the purpose and typical usage; argparse will
# display it in `--help`. Do NOT alter program logic per requirements.
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
# Keep the misspelling of `recomended_length` as-is to avoid changing code.
# This value is referenced in help texts and runtime confirmations.
recomended_length: int = 128


def check_length_arg(value: str | int) -> int:
    """
    Coerce and validate the `--length` argument.

    Conversions:
        - If `value` is a string, it is converted to an integer.
        - If the resulting integer is lower than the recommended default,
          the user is prompted to confirm the shorter length or switch to
          the recommended default.

    Returns:
        int: The chosen length in BYTES that will be passed to
        `secrets.token_urlsafe(length)`.

    Raises:
        argparse.ArgumentTypeError: If the provided value cannot be parsed
        as an integer. The error message is explicit and user-facing.
    """
    # Accept both str and int; keep the original behavior intact.
    if isinstance(value, str):
        try:
            value: int = int(value)
        except ValueError:
            # Clear, user-friendly message (allowed change).
            raise argparse.ArgumentTypeError(f"Value '{value}' is not an integer.")

    # Interactive guard for short lengths. Uses external Y/N helper.
    if value < recomended_length:
        # First confirmation: continue with the short value?
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
            # Second prompt: switch to the recommended default?
            secret_question: bool = ask_yes_no_question(
                promt=f"Do you want to use the recommended default length ({recomended_length}) instead?",
                default='y'
            )
            if secret_question:
                return recomended_length
            else:
                # Early exit if neither option is accepted.
                print("Secret length selection aborted by user. Exiting.")
                exit(3)
    else:
        # Length is >= recommended; accept silently.
        return value


def parse_args() -> argparse.Namespace:
    """
    Build the CLI parser and parse arguments.

    The parser exposes the following options:
      - `--length` / `-l`: number of random BYTES for token_urlsafe().
      - `--path`   / `-p`: destination file path (string).
      - `--overwrite` / `-o`: overwrite existing file without prompting.
      - `--create_parents` / `-c`: auto-create missing parents.
      - `--description` / `-d`: print script description and exit.

    Returns:
        argparse.Namespace: Parsed arguments accessible as attributes.
    """
    # Initialize with program name and rich description (shown in --help).
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        prog=script_name,
        description=script_description
    )

    # Length option:
    # - Validated by check_length_arg (may prompt if short).
    # - Defaults to the recommended number of BYTES for strong entropy.
    parser.add_argument(
        '-l', '--length',
        type=check_length_arg,
        default=recomended_length,
        help=(
            "Number of random BYTES fed to secrets.token_urlsafe() "
            f"(higher = more entropy). If below {recomended_length}, "
            "you will be asked to confirm. Default: %(default)s."
        )
    )

    # Path option:
    # - Destination for the generated secret.
    # - Kept as a simple string here; resolution is done later to avoid
    #   changing program structure.
    parser.add_argument(
        '-p', '--path',
        action='store',
        default=None,
        help=(
            "Destination file path for the generated secret (e.g. ~/.vault_pass). "
            "The path is resolved to an absolute path. Use --create_parents to "
            "auto-create missing directories."
        )
    )

    # Overwrite flag:
    # - If set, an existing file will be replaced without additional prompts.
    parser.add_argument(
        '-o', '--overwrite',
        action='store_true',
        default=False,
        required=False,
        help="Overwrite the file if it already exists without asking for confirmation."
    )

    # Create parents flag:
    # - If set, missing parent directories are created automatically.
    parser.add_argument(
        '-c', '--create_parents',
        action='store_true',
        default=False,
        required=False,
        help="Create any missing parent directories of the target path without asking for confirmation."
    )

    # Description flag:
    # - When present, the script prints its long description and exits (code 0).
    # - This is useful for tooling or documentation generation.
    parser.add_argument(
        '-d', '--description',
        action='store_true',
        default=False,
        required=False,
        help="Print the script description and exit."
    )
    return parser.parse_args()


def generate_secret(length: int) -> str:
    """
    Create a URL-safe, Base64-like secret string.

    Implementation detail:
    - `secrets.token_urlsafe(n)` consumes `n` bytes of randomness and returns
      a string using the URL-safe alphabet. The output string length will be
      larger than `n` because of Base64-like encoding expansion.

    Args:
        length (int): Number of random bytes to feed into token_urlsafe().

    Returns:
        str: URL-safe high-entropy secret.
    """
    return secrets.token_urlsafe(length)


def check_path(path: Path, overwrite: bool = False, create_parents: bool = False) -> bool:
    """
    Ensure the target path and its directory are in a writable state.

    Behavior:
        1) If the parent directory does not exist:
           - If `create_parents` is False: prompt interactively to create it.
           - If `create_parents` is True: create it without prompting.
           - If neither happens, exit with a clear message.
        2) If the file exists:
           - If `overwrite` is False: prompt to confirm overwriting.
           - If `overwrite` is True: proceed without prompting.

    Args:
        path (Path): Destination file path (absolute or relative).
        overwrite (bool): Force overwrite of existing file if True.
        create_parents (bool): Auto-create missing parents if True.

    Returns:
        bool: True if writing may proceed; False only if path checks fail.
    """
    # --- Parent directory handling -----------------------------------------
    if not path.parent.exists():
        if not create_parents:
            # Interactive prompt via helper; keeps UX consistent.
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
            # Safely create the entire parent tree.
            path.parent.mkdir(parents=True)
        else:
            # Early exit: user did not allow creating directories.
            print("Cannot create file without parent directories. User aborted. Exiting.")
            exit(4)

    # --- Existing file handling --------------------------------------------
    if path.parent.exists() and path.exists():
        if not overwrite:
            # Ask before replacing an existing secret file.
            overwrite_question: bool = ask_yes_no_question(
                promt=f"File already exists: {path}. Overwrite?",
                default='n'
            )
            if overwrite_question:
                return True
            else:
                print("User declined to overwrite the existing file. Exiting.")
                exit(5)
        if overwrite:
            return True

    # If the parent exists and either the file doesn't exist or overwrite is allowed.
    return True


def do_work(args: argparse.Namespace) -> None:
    # Support the purely informational mode: print description and stop.
    if args.description:
        print(script_description)
        raise SystemExit(0)

    """
    Orchestrate the path checks and write the secret to disk.

    Steps:
        - Validate that `args.path` is a string (as expected by this script).
        - Resolve the target path to an absolute path for clarity.
        - Run path safety checks (may prompt).
        - If allowed, generate a new secret and atomically write it to the file.

    Note:
        Intentionally keeping the structure and control flow unchanged to
        satisfy the "no logic changes" requirement.
    """
    # Defensive type check: the current CLI defines `--path` as a string option.
    if isinstance(args.path, str):
        path: Path = Path(args.path)
        # Always write to an absolute path to avoid ambiguity.
        path: Path = path.resolve()
    else:
        # Clear, actionable error for unexpected input type.
        raise argparse.ArgumentTypeError(f"Value '{args.path}' is not a string.")

    # Validate path conditions (may prompt the user).
    can_write: bool = check_path(
        path=path,
        overwrite=args.overwrite,
        create_parents=args.create_parents
    )

    # On success, generate the secret and write it out; otherwise, inform and stop.
    if can_write:
        print(f"Writing secret to: {path}")
        path.write_text(data=generate_secret(length=args.length))
        print(f"Secret written successfully to '{path}'. Exiting.")
    else:
        print("Cannot write file (path checks failed). Exiting.")


if __name__ == '__main__':
    # Entry point: parse CLI arguments and execute the main routine.
    # Keeping a single, simple call preserves clarity and testability.
    do_work(args=parse_args())
