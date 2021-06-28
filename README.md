## git-anki

#### Tool for doing version control and collaborative work on your flashcards.

### Usage

Convert all `*.txt` files from directory `dir` to one file `deck.apkg`:

`python main.py release <path/to/dir>`

---

Convert `file.txt` to `deck.apkg`:

`python main.py debug <path/to/file.txt>`

---

Examples of correct `*.txt` files are in directory `example`

### File format

Any lines with only white spaces are ignored.
All white spaces from beginning and end of line are removed.
Files format is as follows:

```
deck_id: *(?'deck_id'[^eol]+)
deck_name: *(?'deck_name'[^eol]+)
file_id: *(?'file_id'[^eol]+)
card_data*
```

Where card_data is made up from 3 lines.

```
<card_id>
<front>
<back>
```

`card_id` should be unique in each file
`file_id` should be unique in each folder
