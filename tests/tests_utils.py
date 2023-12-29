
import unittest
from scripts.utils import \
    create_daily_note, get_daily_note_path, \
    write_to_path, append_to_daily_vault, \
    tree_schema

import os
import datetime
from freezegun import freeze_time
import datetime
import json
import shutil


# Test utils

def set_test_vault_daily_config(config_args={}, overwrite=False):
    # Define defaults here, will be overridden if in config_args
    daily_config_json = {
        "template": ""
    }

    daily_config_json = {**daily_config_json, **config_args}

    config_path = 'test_notes/.obsidian/daily-notes.json'
    
    exists = os.path.exists(config_path)
    if (exists and overwrite) or (not overwrite and not exists): #and not :
        write_to_path(config_path, json.dumps(daily_config_json))

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

    @freeze_time("2023-01-01")
    def test_template_and_append(self):


        set_test_vault_daily_config(
            config_args={'template': self.test_template_path},
            overwrite=True)
        
        # Write test template
        test_template = "## Todo\n\n## Notes\n"
        template_path = os.path.join(
            self.config_vault_path,
            self.test_template_path)
        
        # Make templates dir if it doesn't exist
        parent_dir, _ = os.path.split(template_path)
        if not os.path.exists(parent_dir):
            os.makedirs(parent_dir)

        with open(template_path, 'w') as fh:
            fh.write(test_template)

        # Create daily note
            
        os.environ['daily_note_format'] = "daily_notes/%Y/%m/%d"
        
        create_daily_note(
            self.config_vault_path,
            note_date=datetime.datetime.now())

        # First part of test - Make sure template worked
        assert os.path.exists('test_notes/daily_notes/2023/01/01.md')

        with open('test_notes/daily_notes/2023/01/01.md', 'r') as fh:
            daily_contents = fh.read()
        
        assert daily_contents == test_template

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
        
    

    ## Cases to test
    # - No header
    # - no path
    # - colon in header
    # 
    

if __name__ == '__main__':
    unittest.main()