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
        if not path.parent.exists():
            create_parents: str = input(f'Parents: {path.parents} not exists. Do want to create it? Y/n: ')
            if create_parents.lower() == 'y' or create_parents.lower() == '':
                path.parent.mkdir(parents=True)
            elif create_parents.lower() == 'n':
                print(f'Path: {path} not found. exit')
                exit(1)
            else:
                raise ValueError(f'input was false. abort')
        if path.exists():
            overwrite_file: str = input(f'File: {path} allready exists. Overwrite it? y/N: ')
            if overwrite_file.lower() == 'y':
                return path
            elif overwrite_file.lower() == '' or 'n':
                print('File will not overwritten. exit')
                exit(2)
            else:
                raise ValueError(f'input was false. abort')
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


if __name__ == '__main__':
    args: argparse.Namespace = parse_args()
    print(args)
    #file: Path = args.path
    #file.write_text(data=generate_secret(length=args.length))