def ask_yes_no_question(promt: str, default: str) -> bool:
    if default.lower() == 'y':
        default_str: str = 'Y/n'
        default_value: bool = True
    if default.lower() == 'n':
        default_str: str = 'y/N'
        default_value: bool = False
    question: str = input(f'{promt} {default_str}: ').lower()
    match question:
        case '':
            return default_value
        case 'y':
            return True
        case 'n':
            return False
        case _:
            return False