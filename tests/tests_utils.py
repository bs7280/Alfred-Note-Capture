
import unittest
from scripts.utils import \
    create_daily_note, get_daily_note_path, \
    write_to_path, append_to_daily_vault, \
    tree_schema, find_header_pos, create_obsidian_url, insert_text, read_daily_note

from scripts.note_parser import get_header_sections
import os
import datetime
from freezegun import freeze_time
import datetime
import json
import shutil
from urllib.parse import urlparse
from urllib.parse import parse_qs


# Test utils

def set_test_vault_daily_config(config_args={}, overwrite=False):
    # Define defaults here, will be overridden if in config_args
    daily_config_json = {
        "template": ""
    }

    daily_config_json = {**daily_config_json, **config_args}

    config_path = 'test_notes/.obsidian/daily-notes.json'
    
    exists = os.path.exists(config_path)
    if (exists and overwrite) or (not exists): #and not :
        write_to_path(config_path, json.dumps(daily_config_json))

# Test data 
        
fake_note_01 = \
"""## Todo

- foobar

## Ideas

- get rich

## Notes

"""

# Tests

class TestUtils(unittest.TestCase):
    config_vault_path = 'test_notes/'
    test_template_path = 'templates/daily-note.md'
    
    def setUp(self):
        set_test_vault_daily_config()

    def tearDown(self) -> None:
        # Delete and recreate as empty note vault 
        shutil.rmtree('test_notes/')
        os.makedirs('test_notes/')

        return super().tearDown()

    @freeze_time("2023-01-01")
    def test_get_daily_path(self):
        os.environ['daily_note_format'] = "%Y-%m-%d"

        daily_path = get_daily_note_path(self.config_vault_path, note_date=datetime.datetime.now())

        assert daily_path == 'test_notes/2023-01-01.md'

    @freeze_time("2023-01-01")
    def test_get_daily_folder(self):
        os.environ['daily_note_format'] = "foobar/%Y-%m-%d"

        daily_path = get_daily_note_path(self.config_vault_path, note_date=datetime.datetime.now())

        assert daily_path == 'test_notes/foobar/2023-01-01.md'

    @freeze_time("2023-01-01")
    def test_create_daily_note(self):
        os.environ['daily_note_format'] = "%Y-%m-%d"
        
        create_daily_note(self.config_vault_path, note_date=datetime.datetime.now())

        assert os.path.exists('test_notes/2023-01-01.md')

    @freeze_time("2023-01-01")
    def test_create_daily_note_with_space(self):
        os.environ['daily_note_format'] = "Notes %Y/%m-%d"
        
        create_daily_note(
            self.config_vault_path,
            note_date=datetime.datetime.now())

        assert os.path.exists('test_notes/Notes 2023/01-01.md')

    @freeze_time("2023-01-01")
    def test_create_daily_note_with_extension(self):
        os.environ['daily_note_format'] = "%Y-%m-%d.md"
        
        create_daily_note(
            self.config_vault_path,
            note_date=datetime.datetime.now())

        assert os.path.exists('test_notes/2023-01-01.md')

    @freeze_time("2023-01-01")
    def test_create_daily_note_folder(self):
        os.environ['daily_note_format'] = "foobar/%Y-%m-%d"
        
        create_daily_note(
            self.config_vault_path,
            note_date=datetime.datetime.now())

        assert os.path.exists('test_notes/foobar/2023-01-01.md')


class TestModifyNote(TestUtils):
    test_template = "## Todo\n\n## Notes\n"

    @freeze_time("2023-01-01")
    def setUp(self):
        set_test_vault_daily_config(
            config_args={'template': self.test_template_path},
            overwrite=True)

        # Write test template
        template_path = os.path.join(
            self.config_vault_path,
            self.test_template_path)
        
        # Make templates dir if it doesn't exist
        parent_dir, _ = os.path.split(template_path)
        if not os.path.exists(parent_dir):
            os.makedirs(parent_dir)

        with open(template_path, 'w') as fh:
            fh.write(self.test_template)

        # Create daily note
        os.environ['daily_note_format'] = "daily_notes/%Y/%m/%d"
        create_daily_note(
            self.config_vault_path,
            note_date=datetime.datetime.now())
        
        # First part of test - Make sure template worked
        assert os.path.exists('test_notes/daily_notes/2023/01/01.md'), \
            "Test Setup failed to reach desired state - daily path doesn't exist"
        
    @freeze_time("2023-01-01")
    def test_get_daily_template(self):
        pass

    @freeze_time("2023-01-01")
    def test_template_and_append(self):
        # First part of test - Make sure template worked
        assert os.path.exists('test_notes/daily_notes/2023/01/01.md')

        with open('test_notes/daily_notes/2023/01/01.md', 'r') as fh:
            daily_contents = fh.read()
        
        assert daily_contents == self.test_template

        ## Test append
        append_text = f'- Foo the baz'
        append_to_daily_vault(
            self.config_vault_path,
            '## Todo',
            append_text
            )

        with open('test_notes/daily_notes/2023/01/01.md', 'r') as fh:
            daily_contents = fh.read()

        assert daily_contents.split('\n')[2] == append_text

    @freeze_time("2023-01-01")
    def test_insert(self):
        content = '## Todo'
        new_text = insert_text(self.config_vault_path, '## Todo', 'a thing')
        assert 'a thing' in new_text.split('\n')

    # ERROR CASE
    @freeze_time("2023-01-01")
    def test_insert_to_missing_header(self):
        
        with self.assertRaises(ValueError):
            new_text = insert_text(self.config_vault_path, '## Bazfoo', 'a thing')

    # ERROR CASE
    @freeze_time("2023-01-01")
    def test_insert_incorrect_header_level(self):    
        with self.assertRaises(ValueError):
            new_text = insert_text(self.config_vault_path, '# Todo', 'a thing')
            assert 'a thing' in new_text.split('\n')

    # ERROR CASE
    @freeze_time("2023-01-01")
    def test_insert_case_sensitive_header(self):
        with self.assertRaises(ValueError):
            new_text = insert_text(self.config_vault_path, '## todo', 'a thing')
            assert 'a thing' in new_text.split('\n')

    # ERROR CASE
    @freeze_time("2023-01-01")
    def test_insert_without_space_in_header(self):
        
        with self.assertRaises(ValueError):
            new_text = insert_text(self.config_vault_path, '##Todo', 'a thing')
            assert 'a thing' in new_text.split('\n')

    @freeze_time("2023-01-01")
    def test_insert_create_header(self):

        new_text = insert_text(
            self.config_vault_path,
            '## Bazfoo', 'a thing',
            create_header_if_missing=True)
        
        assert '## Bazfoo' in new_text.split('\n')
        assert 'a thing' in new_text.split('\n')

        # Write to daily path
        daily_path = get_daily_note_path(self.config_vault_path)
        write_to_path(daily_path, new_text)

        # Insert again with same params
        new_text = insert_text(
            self.config_vault_path,
            '## Bazfoo', 'a second thing',
            create_header_if_missing=True)
        
        lines = new_text.split('\n')
        assert lines.index('## Bazfoo') == 4
        assert lines.index('a thing') + 1 == lines.index('a second thing')
  
    @freeze_time("2023-01-01")
    def test_append_to_daily(self):
        append_to_daily_vault(self.config_vault_path,
            '## Todo', 'a thing',
            create_header_if_missing=True)
        
        lines = read_daily_note(self.config_vault_path).split('\n')
        assert 'a thing' in lines
        assert '## Foobar' not in lines

        append_to_daily_vault(self.config_vault_path,
            '## Foobar', 'a different thing',
            create_header_if_missing=True)

        assert 'a thing' in lines
        assert '## Foobar' not in lines
        

class TestGetHeader(unittest.TestCase):
    config_vault_path = 'test_notes/'
    test_template_path = 'templates/daily-note.md'

    def setUp(self) -> None:
        return super().setUp()
    
    def tearDown(self) -> None:
        return super().tearDown()
    
    def test_basic_get_pos(self):

        start_line, end_line = find_header_pos(fake_note_01, '## Todo')
        assert (start_line, end_line) == (0, 2)

        start_line, end_line = find_header_pos(fake_note_01, '## Ideas')
        assert (start_line, end_line) == (4, 6)

        start_line, end_line = find_header_pos(fake_note_01, '## Notes')
        #breakpoint()
        assert (start_line, end_line) == (8, None)

    def test_get_all_header_pos(self):
        out = get_header_sections(fake_note_01)
        
        assert '## Todo' in out.keys()
        assert '## Ideas' in out.keys()
        assert '## Notes' in out.keys()

        assert out['## Todo'] == (0, 3)

        lines = fake_note_01.split('\n')

        assert '- foobar' in lines[out['## Todo'][0]:out['## Todo'][1]]
        assert '- get rich' in lines[out['## Ideas'][0]:out['## Ideas'][1]]

        assert '' in lines[out['## Notes'][0]:out['## Notes'][1]]

        #breakpoint()

class TestGlobSearch(unittest.TestCase):
    config_vault_path = 'test_notes/'

    def setUp(self) -> None:
        # Define fake filenames and contents for test vault
        file_mapper = {
            'code.python.snippets.md': '## Datetime\n\n##Os walk',
            'code.python.lib.pandas.md': '## Add a column\n\n## Get first n rows',
            'code.python.lib.numpy.md': '## Make a random array\n\n## Make a random matrix',
            'code.sql.lib.foobar.md': '## SQL\n',
            'nothing.md': 'No headers',
            'empty.md': 'empty',
            'Notes 2023/01-01.md': '## TODO\n\n - foo the bar\n- buy milk',
            'Notes 2022/01-01.md': '## TODO\n\n - foo the bar\n- buy milk',
        }

        # Write all files to test dir
        for fname, contents in file_mapper.items():
            fpath = os.path.join(self.config_vault_path, fname)
            write_to_path(fpath, contents)

        return super().setUp()
    
    def tearDown(self) -> None:
        # Delete and recreate as empty note vault 
        shutil.rmtree('test_notes/')
        os.makedirs('test_notes/')

        return super().tearDown()
    
    # Test searching on only fname
    def test_01(self):
        search_query = "python"
        out = tree_schema(self.config_vault_path, search_query)

        assert len(out) == 5

    # Test searching on only header
    def test_02(self):
        search_query = "*:Datetime"
        out = tree_schema(self.config_vault_path, search_query)
        assert len(out) == 1

        ## Search lowercase
        search_query = "*:datetime"
        out_lower = tree_schema(self.config_vault_path, search_query)
        
        assert len(out) == 1
        assert out == out_lower
    
    # Search with file and header
    def test_03(self):
        search_query = "python:datetime"
        out = tree_schema(self.config_vault_path, search_query)

        assert len(out) == 1

    def test_04(self):
        search_query = "code.*.lib.*"
        out = tree_schema(self.config_vault_path, search_query)

        assert len(out) == 5
        assert len(set([x['subtitle'].split(':')[0] for x in out])) == 3

    def test_05(self):
        search_query = "nothing"
        out = tree_schema(self.config_vault_path, search_query)

        assert len(out) == 1
        assert len(set([x['subtitle'].split(':')[0] for x in out])) == 1

    def test_06(self):
        search_query = "empty"
        out = tree_schema(self.config_vault_path, search_query)
        assert len(out) == 1
        assert len(set([x['subtitle'].split(':')[0] for x in out])) == 1

    def test_07(self):
        search_query = ":Random"
        out = tree_schema(self.config_vault_path, search_query)
        assert len(out) == 2
        assert len(set([x['subtitle'].split(':')[0] for x in out])) == 1
        
    def test_search_and_get_url(self):
        search_query = "python:Datetime"
        out = tree_schema(self.config_vault_path, search_query)
        #fname, header = out[0]['arg'].split(':')
        #url = create_obsidian_url(self.config_vault_path, fname, heading=header)
        
        url = out[0]['arg']

        assert 'obsidian://advanced-uri?' in url
        assert len(out) == 1

        # Validate that no # in heading part of arg
        parsed_url = urlparse(url)
        captured_value = parse_qs(parsed_url.query).get('heading')[0]

        assert '#' not in captured_value
        #breakpoint()

    ## Cases to test
    # - No header
    # - no path
    # - colon in header
    # 
    

if __name__ == '__main__':
    unittest.main()