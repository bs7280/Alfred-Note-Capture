# Alfred Note Capture
An [Alfred](https://www.alfredapp.com/) workflow for capturing ideas, notes, links, todos, and even browser tabs directly to your notes without context switching.

## Setup 
Shimmering obsidian required to use the search notes command - `f <query>`

Workflow configuration:
1. Set all variables
    - vault path
    - daily note format
2. Setup daily note template. Currently, the workflow requires some hard coded headers as shown below. In the future I plan to make this configurable.


Copy the following into your dailynote template. Note - you **CAN** Add more content above and below these headers. The workflow looks for an H2 of Todo/Ideas/Journal/Bookmakrs.

```
## Todo

## Ideas

## Journal

## Bookmarks

## Other
```

## Features
- Browser related:
    - Copy current browser tab as a markdown link
    - Append current browser tab to your daily notes
        - Default (`Return`) is for `## Bookmarks` header
        - `Shift+return` for Todo header
        - `Control+return` for Ideas header
    - Search current browser tab in your notes
- Thought capture:
    - `ji` Append a bullet to `## Ideas` header
    - `jj` Append a bullet to `## Journal` header
    - `jt` Append to `## Todo` header
- Experimental: 
    - `nf <search query>` to search your notes for a given string. 
        - Not well optimized
        - Requires command 'mdfind' to be in path (future improvement will fix).
        - Requires shimmering obsidian workflow to open note (future improvement will fix)
    - `ns <path glob filter>:<header glob filter>` to search path and headers in notes
        - not well optimized, reads all your notes every search.
        - `python:datetime` will return all files with python in name and headers with datetime
        - `code/*/snippets:##*` will return all h2+ headers in any code snippet file

Experimental features may require extra setup or change in next update. Feedback or ideas are highly encouraged.

## Examples

### Append A URL to daily note
![Alt Text](gifs/append_url.gif)

### Append A URL to my Todos
![Alt Text](gifs/append_todo_url.gif)

### Insert a journal note
![Alt Text](gifs/insert_journal_note.gif)

### Insert a todo note
![Alt Text](gifs/insert_todo_note.gif)


## Future changes / todo
- Optimize note search
- optimize note find
- Implement open in obsidian for note find
- support note search query with appending text to a specific place