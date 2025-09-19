import argparse
import os

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
        file: str = value.split('/')[len(value.split('/')) - 1]
        path: str = value.strip(f'/{file}')
        if path == '.' or path == '..':
            path = os.path.abspath(path=f'{path}/')
        print(file)
        print(path)
        return value
    else:
        raise argparse.ArgumentTypeError(f"'{value}' ist kein String")

def parse_args() -> argparse.Namespace:
    parser: argparse.ArgumentParser = argparse.ArgumentParser(prog=script_name, description=script_description)
    parser.add_argument('--length', type=check_length_arg, default=check_length_arg(value=16), help='')
    parser.add_argument('path', type=check_path_arg, help='')
    return parser.parse_args()


if __name__ == '__main__':
    args: argparse.Namespace = parse_args()
    print(args)