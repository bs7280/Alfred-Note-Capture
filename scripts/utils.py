import os
import datetime
from typing import Optional
import json
import re
import sys
import glob
import fnmatch
import subprocess
from urllib.parse import quote

## Default values
default_daily_template = """
## Todo

## Ideas

## Journal

## Bookmarks

## Other
"""

## Methods

def get_daily_note_path(vault_path, note_date: Optional[datetime.datetime]=None):

    if note_date is None:
        note_date = datetime.datetime.now()

    daily_note_format = os.environ.get('daily_note_format')


    daily_note_path = f'{note_date.strftime(daily_note_format)}'

    if daily_note_path[-3:] != '.md':
        daily_note_path = daily_note_path + '.md'
    return os.path.join(vault_path, daily_note_path)

def write_to_path(note_path, content):
    parent_dir, _ = os.path.split(note_path)
    if not os.path.exists(parent_dir):
        os.makedirs(parent_dir)

    with open(note_path, 'w') as f_daily:
        f_daily.writelines(content)
        f_daily.close()

def create_daily_note(vault_path, note_date: Optional[datetime.datetime]=None):

    if note_date is None:
        note_date = datetime.datetime.now()

    daily_path = get_daily_note_path(vault_path, note_date=note_date)

    if not os.path.exists(daily_path):
        template_location = get_daily_template(vault_path)

        if template_location and os.path.exists(template_location):
            with open(template_location, 'r') as f:
                template_text = f.read()
        else:
            sys.stderr.write(f"Warning - could not find daily template location: {template_location} using default daily template")
            template_text = default_daily_template
        
        # Write to file daily_path
        write_to_path(daily_path, template_text)

    # Returns daily_path it created
    return daily_path

def get_daily_template(vault_path):
    path = os.path.join(vault_path, '.obsidian/daily-notes.json')

    if not os.path.exists(path):
        sys.stderr.write(
            f"Warning couldn't find daily note config `daily-notes.json` file at {path}",
            file=sys.stderr)
        return None
    else:
        with open(path, 'rb') as f:
            content = json.loads(f.read())

    if 'template' in content:
        rel_path = content['template']
        if rel_path != '':
            return os.path.join(vault_path, rel_path)
        else:
            sys.stderr.write('Warning, key `template` exists in dailynote config but is empty str, not using daily template')
            return None
    else:
        sys.stderr.write(f"Error, key `template` not in daily-notes.json file {path}, not using a daily template. Content of config: {content}")
        return None

def read_daily_note(vault_path):
    daily_path = get_daily_note_path(vault_path)

    with open(daily_path, 'r') as f:
        daily_content = f.read()
        f.close()

    return daily_content

# TODO will replace this with alternative method in note_parser.py
def find_header_pos(note_content, header_str):
    
    # Find headers
    regex_md_header = r'^#+ .+$'

    matches = [x.group() for x in re.finditer(regex_md_header, note_content, re.M)]

    if header_str not in matches:
        sys.stderr.write(f"Warning: Could not find header `{header_str}` in {matches}")
        return None, None

    start_line = None
    end_line = None

    lines = note_content.split('\n')

    for i, line in enumerate(lines):
        if start_line is None:
            if line == header_str:
                start_line = i
                break

    # Last non empty
    for i, line in enumerate(lines[start_line:]):
        if line == header_str:
            pass
        elif line in matches:
            #end_line = (start_line + i)
            break
        elif line != '':
            end_line = start_line + i

    if start_line is None:
        raise ValueError(f"Unexpected edge case - Could not find already matched header {header_str}")
    
    return start_line, end_line
    

def insert_text(vault_path, header, inserted_text, create_header_if_missing=False):
    """
    Python implementation of https://github.com/chrisgrieser/shimmering-obsidian/blob/main/scripts/append-to-note.js

    Returns new text as string, does not modify the file
    """
    note_content = read_daily_note(vault_path)

    start_line, end_line = find_header_pos(note_content, header)
    lines = note_content.split('\n')

    if start_line is None:
        if create_header_if_missing:
            sys.stderr.write(f"Could not find header {header} in daily note, creating it at end of note")

            ## Add desired header to end of document
            lines.insert(len(lines), header)
            # Update header
            start_line = len(lines)
        else:
            raise ValueError(f"Header {header} not found in daily note")

    def ensure_empty_line(line_num, lines):
        if line_num >= len(lines) or lines[line_num] != '':
            lines.insert(line_num, '')

    if end_line is None:
        ensure_empty_line(start_line + 1, lines)
        lines.insert(start_line + 2, inserted_text)
        ensure_empty_line(start_line + 3, lines)
    else:
        lines.insert(end_line + 1, inserted_text)

    return '\n'.join(lines)

def append_to_daily_vault(vault_path, header, message, create_header_if_missing=False):
    new_text = insert_text(
        vault_path, header, message,
        create_header_if_missing=create_header_if_missing)
    daily_path = get_daily_note_path(vault_path)
    write_to_path(daily_path, new_text)

def get_headers_index(filenames):
    """
    Given a list of markdown files, return dict with list of headers in each file
    """
    pattern = r"^(#{1,6})\s(.+)$"

    pattern = r"^#{1,6}\s.+$"

    out = {} # fname: [headers]
    for filename in filenames:
        if filename.endswith('.md'):
            with open(filename, 'r') as f:
                content = f.read()
            matches = re.findall(pattern, content, re.MULTILINE)

            out[filename] = matches
    return out

# TODO - rename this
# Meant to handle 'note.name.*.cheat:## Foobar
# note.path:# *python*
def tree_schema(vault_path, query):

    ## Function split 1 - convert query to glob strings
    if ':' not in query:
        #raise ValueError("Must contain a `:`")
        sys.stderr.write("no `:` found in query str, treating as path glob search")
        path_q = query
        tree_q = None
    else:
        # Path query is glob searching on filename
        # tree query is glob searching on headers
        path_q, tree_q = query.split(':')

    ## Pad each of path/tree query str with a `*` for easier clob usage
    if path_q:
        if path_q[0] != '*':
            path_q = '*' + path_q
        if path_q[-1] != '*':
            path_q =  path_q + '*'

    if tree_q:
        # Pad tree query
        if tree_q[0] != '*':
            tree_q = '*' + tree_q
        if tree_q[-1] != '*':
            tree_q =  tree_q + '*'

    # Find path_q

    # Step 0 - get index of 
    # TODO - cache this result eventually, will be slow for big vaults
    headers_index = get_headers_index(glob.glob(os.path.join(vault_path, '*'), recursive=True))

    ## Step 1 - Filter out files that match fname part of glob query
    if path_q:
        path_glob = os.path.join(vault_path, path_q)
        searched_files = glob.glob(path_glob, recursive=True)
        # Only get items from headers based on filenames (keys) in searched_files
        subset_headers = dict((k, headers_index[k]) for k in searched_files if k in headers_index)
    else:
        # No file related search query given, use all files for search canidates
        subset_headers = headers_index

    #combined_strings = [item for filename, items in subset_headers.items() for item in items]
    # Format out: `/path/to/vault/note-name.md:# Header In markdown file`
    # Kindof insane long one liner - last if statement block is to handle edge case of a note not having
    # any headers
    combined_strings = [f"{filename}:{item}" for filename, items in subset_headers.items() for item in (items if len(items) > 0 else [''])]

    # Filter out matched file's header's with tree query glob
    if tree_q:
        # Create regex out of fmatch glob
        globexpression = f'*:{tree_q}'
        reg_expr = re.compile(fnmatch.translate(globexpression), re.IGNORECASE)
        matches = [f for f in combined_strings if re.match(reg_expr, f)]

        #matches = fnmatch.filter(combined_strings, f'*:{tree_q}')
    else:
        matches = combined_strings

    # match on headers
    out = []
    for match in matches:
        if ':' not in match:
            sys.stderr.write(f"Can't split fname `{fname}` from full path `{match}`")
        else:
            # get filname off of string before splitting parent dir + filename
            basename = match.split(':')[0]
            # Joins again to handle edge case of a colon being in markdown header
            header = ':'.join(match.split(':')[1:])

            dir, fname = os.path.split(basename)

        out.append({
            'title': f'{fname}:{header}' if len(header) > 1 else fname,
            'subtitle': fname,
            'arg': create_obsidian_url(
                vault_path, fname,
                heading=(header if len(header) > 1 else None)),
        })

    return out

def create_obsidian_url(vault_path, relative_path, heading=None, line_num=None):
    relative_path_enc = quote(relative_path)

    vault_path = os.path.split(vault_path)[1]
    vault_name_enc = quote(vault_path.replace("/", "/"))
    url_scheme = f"obsidian://advanced-uri?vault={vault_name_enc}&filepath={relative_path_enc}"
    if heading:
        # Heading can't have # symbol
        # https://vinzent03.github.io/obsidian-advanced-uri/actions/navigation
        # ^ Docs
        header = heading.replace('#', '').strip()
        url_scheme += f"&heading={quote(header)}"
    elif line_num:
        url_scheme += f"&line={quote(line_num)}"


    return url_scheme
    #subprocess.call(['open', url_scheme])

#### Run

if __name__ == '__main__':
    ## Config
    vault_path = '~/Documents/personalvault-1/'

    if '~' in vault_path:
        vault_path = os.path.expanduser(vault_path)

    if False:
        daily_note_format = '%Y-%m-%d'

        create_daily_note(vault_path)

        append_to_daily_vault(vault_path, '## Todo', f'- Foo the baz')
        append_to_daily_vault(vault_path, '## Other', f'- Foo the baz')
    else:
        #write_to_path(os.path.join(vault_path, 'code.python.snippets'))
        #write_to_path(os.path.join(vault_path, 'code.sql.snippets'))
        #write_to_path(os.path.join(vault_path, 'code.js.snippets'))


        #out = tree_schema(vault_path, 'code.*.snippets*:*datetime*')
        #out = tree_schema(vault_path, 'code.*.snippets*:')
        out = tree_schema(vault_path, 'python')

        breakpoint()
        #url = create_obsidian_url(vault_path, )

        print(out)





# uri = "obsidian://open?path=" + encodeURIComponent(filepath)

