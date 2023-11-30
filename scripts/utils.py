import os
import datetime
from typing import Optional
import json
import re

## Methods
daily_note_format = os.environ.get('daily_note_format')

def get_daily_note_path(vault_path, note_date: Optional[datetime.datetime]=datetime.datetime.now()):
    daily_note_path = f'{note_date.strftime(daily_note_format)}.md'
    return os.path.join(vault_path, daily_note_path)

def write_daily_path(daily_path, content):
    with open(daily_path, 'w') as f_daily:
        f_daily.writelines(content)
        f_daily.close()


def create_daily_note(vault_path, note_date: Optional[datetime.datetime]=datetime.datetime.now()):
    daily_path = get_daily_note_path(vault_path, note_date=note_date)

    if not os.path.exists(daily_path):
        template_location = get_daily_template(vault_path)

        with open(template_location, 'r') as f:
            template_text = f.read()
        
        # Write to file daily_path
        write_daily_path(daily_path, template_text)

def get_daily_template(vault_path):
    path = os.path.join(vault_path, '.obsidian/daily-notes.json')

    with open(path, 'rb') as f:
        content = json.loads(f.read())
        f.close()

    rel_path = content['template']

    return os.path.join(vault_path, rel_path)

def read_daily_note(vault_path):
    daily_path = get_daily_note_path(vault_path)

    with open(daily_path, 'r') as f:
        daily_content = f.read()
        f.close()
    
    return daily_content

def insert_text(vault_path, header, content):
    """
    Python implementation of https://github.com/chrisgrieser/shimmering-obsidian/blob/main/scripts/append-to-note.js
    """
    daily_content = read_daily_note(vault_path)

    # Find headers
    regex_md_header = r'^#+ .+$'

    matches = [x.group() for x in re.finditer(regex_md_header, daily_content, re.M)]

    if header not in matches:
        raise ValueError(f"Could not find header `{header}`")

    start_line = None
    end_line = None

    lines = daily_content.split('\n')

    for i, line in enumerate(lines):
        if start_line is None:
            if line == header:
                start_line = i
                break

    # Last non empty
    last_line = -1
    for i, line in enumerate(lines[start_line:]):
        if line == header:
            pass
        elif line in matches:
            break
        elif line != '':
            last_line = start_line + i

    if start_line is None:
        raise ValueError("Could not find already matched header")
    
    def ensure_empty_line(line_num, lines):
        if line_num >= len(lines) or lines[line_num] != '':
            lines.insert(line_num, '')

    if last_line == -1:
        ensure_empty_line(start_line + 1, lines)
        lines.insert(start_line + 2, content)
        ensure_empty_line(start_line + 3, lines)
    else:
        lines.insert(last_line + 1, content)

    return '\n'.join(lines)

def append_to_daily_vault(vault_path, header, message):
    new_text = insert_text(vault_path, header, message)
    daily_path = get_daily_note_path(vault_path)
    write_daily_path(daily_path, new_text)


#### Run

if __name__ == '__main__':
    ## Config
    vault_path = '~/Documents/personalvault-1/'

    if '~' in vault_path:
        vault_path = os.path.expanduser(vault_path)

    daily_note_format = '%Y-%m-%d'

    create_daily_note(vault_path)

    append_to_daily_vault(vault_path, '## Todo', f'- Foo the baz')
    append_to_daily_vault(vault_path, '## Other', f'- Foo the baz')




# uri = "obsidian://open?path=" + encodeURIComponent(filepath)

