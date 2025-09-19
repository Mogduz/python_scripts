import argparse
from pathlib import Path
import secrets

script_name: str = 'create_ansible_vault_pass_file'
script_description: str = ''
valid_lengths: list = [16, 32, 64, 128]

def check_length_arg(value: str | int) -> int:
    if isinstance(value, str):
        try:
            value: int = int(value)
        except ValueError:
            raise argparse.ArgumentTypeError(f"'{value}' ist keine ganze Zahl")
        
    if value not in valid_lengths:
        raise argparse.ArgumentTypeError(f"Wert muss einem der Werte {valid_lengths} entsprechen")
    return value

def check_path_arg(value: str) -> str:
    if isinstance(value, str):
        path: Path = Path(value)
        path: Path = path.resolve()
        return path
    else:
        raise argparse.ArgumentTypeError(f"'{value}' ist kein String")

def parse_args() -> argparse.Namespace:
    parser: argparse.ArgumentParser = argparse.ArgumentParser(prog=script_name, description=script_description)
    parser.add_argument('--length', type=check_length_arg, default=check_length_arg(value=16), help='')
    parser.add_argument('path', type=check_path_arg, help='')
    parser.add_argument('--overwrite', action='store_true', default=False, required=False, help='')
    parser.add_argument('--create_parents', action='store_true', default=False, required=False, help='')
    return parser.parse_args()

def generate_secret(length: int) -> str:
    return secrets.token_urlsafe(length)

def check_path(path: Path, overwrite: bool = False, create_parents: bool = False) -> bool:
    if not path.parent.exists():
        if not create_parents:
            create_parents_question: str = input(f'Parent directories: {path.parents} not exists. Do want to create it? Y/n: ').lower()
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
            path.parent.mkdir(parents=True)
    if path.parent.exists() and not path.exists():
        file_ok: bool = True
    if path.parent.exists() and path.exists():
        if not overwrite:
            overwrite_question: str = input(f'file: {path} allready exists. Overwrite? y/N: ').lower()
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
    if path.parent.exists() and path.exists() and overwrite:
        file_ok: bool = True
    if path.parent.exists() and path.exists() and not overwrite:
        file_ok: bool = False
    if path.parent.exists() and file_ok:
        return True
    return False

def do_work(args: argparse.Namespace) -> None:
    can_write: bool = check_path(path=args.path, overwrite=args.overwrite, create_parents=args.create_parents)
    print(args)
    print(can_write)

if __name__ == '__main__':
    do_work(args=parse_args())
    #file: Path = args.path
    #file.write_text(data=generate_secret(length=args.length))