import re

def get_header_sections(text):
    """ Given markdown text, return:
    {
        'header': (start_line, end_line),
        ...
    }

    for all headers

    Notes:
    Sub header's lines wont be included in parent header.
    For now that's fine, but requirements could be changed later
    
    Generated with LLM from Phind.com v9 model
    """

    # Split the text into lines
    lines = text.split('\n')

    # Initialize a list to store the header sections
    header_sections = []

    # Initialize variables to keep track of the current header section and its level
    current_header = None
    current_level = None
    current_header_start = None

    # Iterate over each line
    for i, line in enumerate(lines):
        # Check if the line starts with a hash sign
        if line.startswith('#'):
            # Extract the level of the header (i.e., the number of '#' signs)
            level = len(re.match('#*', line).group())

            # If it does, and there is a current header section, add it to the list
            if current_header is not None and level <= current_level:
                header_sections.append((current_header, (current_header_start, i - 1)))

            # Start a new header section
            current_header = line.strip()
            current_level = level
            current_header_start = i

    # Add the last header section to the list
    if current_header is not None:
        header_sections.append((current_header, (current_header_start, len(lines) - 1)))

    return dict(header_sections)
        