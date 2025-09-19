import argparse

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

def parse_args() -> argparse.Namespace:
    parser: argparse.ArgumentParser = argparse.ArgumentParser(prog=script_name, description=script_description)
    parser.add_argument('length', action=check_length_arg, default=16, help='')
    return parser.parse_args()


if __name__ == '__main__':
    args: argparse.Namespace = parse_args()
    print(args)