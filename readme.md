Simple program to create audiobooks from text files using Google Text-to-Speech. It works around the 5000 character limit by splitting the text into chunks. The chunks are then combined into a single M4A file.

This expects the files to be in the `book_chapters` directory. The files should be named like `Chapter 00 Introduction.txt`, `Chapter 01 First Chapter.txt`, etc.

Change the `author` and `album` variables in the `audiobook_create.py` file to your desired values. Also change the `voice` variable to the voice you want to use.