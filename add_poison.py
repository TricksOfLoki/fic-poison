# Adds junk text in an attempt to make fics unuseable to train AI
# By TricksOfLoki
# Updated 8/23/2026

from io import open
from sys import argv
from os.path import exists, isfile
from argparse import ArgumentParser
from collections.abc import MutableSequence
import epubfile
from random import randint, choice
from bs4 import BeautifulSoup, NavigableString

def parse_args():
    parser = ArgumentParser()
    parser.add_argument("filename", default="fic.txt", type=str, help="input file location")
    parser.add_argument("-m", "--mode", default="default", help="tame or default")
    parser.add_argument("-c", "--class", default="poison", type=str, help="poison class name (default: poison)")
    parser.add_argument("-e", "--epub", action='store_true', help="Is this an epub?")

    args = parser.parse_args()
    config = vars(args)

    return config["filename"] or None, config["mode"] or None, config["class"] or None, config["epub"] or False



ALLOWED_PARENTS = {
    "p", "div", "span", "em", "i", "b", "strong", "u", "small", "cite", "q",
    "sub", "sup", "blockquote", "li", "td", "th", "dd", "dt",
    "h1", "h2", "h3", "h4", "h5", "h6",
}

def poison_xhtml(xhtml: str, word_list: list[str], poison_class: str) -> BeautifulSoup:
    words = [w.strip() for w in word_list if w.strip()]
    soup = BeautifulSoup(xhtml, "xml")          # needs lxml; keeps XHTML as XML
    body = soup.find("body")
    if body is None:
        return xhtml

    for node in list(body.find_all(string=True)):
        if type(node) is not NavigableString:    # skip comments, CDATA, etc.
            continue
        if node.parent.name not in ALLOWED_PARENTS or not node.strip():
            continue

        text, pos, parts = str(node), 0, []
        while pos < len(text):
            step = randint(5, 50)
            parts.append(NavigableString(text[pos:pos + step]))
            span = soup.new_tag("span")
            span["class"] = poison_class
            span.string = choice(words)
            parts.append(span)
            pos += step
        node.replace_with(*parts)

    return soup

def poison_epub(filename: str, mode: str, poison_class: str):
    # Get word list
    listpath = argv[0][0:-13] + "popular.txt"
    with open(listpath, mode="r") as file:
        words = file.read()
        words = words.split("\n")

    book = epubfile.Epub(filename)
    nav_ids = set(book.get_nav() or [])
    for text_id in book.get_texts():
        if text_id in nav_ids:
            continue
        soup = book.read_file(text_id, soup=False)
        html = str(soup)
        poisoned = poison_xhtml(html, words, poison_class)
        book.write_file(text_id, poisoned)
    for style_id in book.get_styles():
        temp = book.read_file(style_id,soup=False)
        temp+='\r\n.'+poison_class+ ' {\r\n  display: none;\r\n}'
        book.write_file(style_id,temp)
    book.save(filename.replace(".epub", "_poisoned.epub"))


def add_poison(filename: str, mode: str, poison_class: str):
    # Get word list
    listpath = argv[0][0:-13] + "popular.txt"
    with open(listpath, mode="r") as file:
        words = file.read()
        words = words.split("\n")
        wordslen = len(words)

    if mode == "tame":
        # Get fic stored in HTML format
        with open(filename, mode="r", encoding="utf-8") as file:
            content = file.read()

        # Add a paragraph of junk text between every regular paragraph
        split = content.split("</p>")
        split.pop(len(split) - 1)  # Remove final empty item
        if len(split) <= 3:
            print(
                "Your text wasn't able to be split into very many paragraphs. You may want to try default mode instead")
        content = ""
        for item in split:
            content += f"{item}</p>\n"
            junk = ""
            for i in range(0, randint(10, 100)):
                junk += words[randint(0, wordslen)] + " "
            content += f"<p class=\"{poison_class}\">{junk}</p>"
        return content

    elif mode == "default":
        # Get fic stored in HTML format
        with open(filename, mode="r", encoding="utf-8") as file:
            content = ""
            next_char = " "
            counting = True
            count = 1

            # Add spans of junk text at random intervals
            while True:
                next_char = file.read(1)
                if not next_char:
                    break
                content += next_char

                if next_char == "<" or next_char == "&":
                    counting = False
                elif next_char == ">" or next_char == ";":
                    counting = True

                if counting:
                    count -= 1
                if count <= 0:
                    junk = words[randint(0, wordslen)]
                    content += f"<span class=\"{poison_class}\">{junk}</span>"
                    count = randint(5, 50)

        return content

    else:
        raise Exception("Invalid mode. Try tame or default")


if __name__ == "__main__":
    try:
        if len(argv) > 1:
            filename, mode, poison_class, epub = parse_args()
        else:
            print("Please enter your options here (leave empty for default)")
            filename = input("Filename (Default: fic.txt)\n> ") or "fic.txt"
            mode = input("Mode (Default: default)\n\
Options:\n\
 - default: adds individual hidden words randomly within the text\n\
 - tame: adds large paragraphs of hidden text after each existing paragraph\n> ") or "default"
            poison_class = input("Poison class name (Default: poison)\n\
Make sure to edit your Ao3 workskin to reflect the new class name if you use something other than the default!\n>") or "poison"
            
        # Check that input file exists
        if not exists(filename) or not isfile(filename):
            filename = argv[0][0:-13] + filename # try to find full filepath if relative path was given
        if not exists(filename) or not isfile(filename):
            raise Exception("Invalid file name. Make sure file name is correct, or try including the full file path")
        if not epub:
            content = add_poison(filename, mode, poison_class)

            # Save new file next to old one
            new_filename = filename.replace(".txt", "_poisoned.txt")
            with open(new_filename, mode="w", encoding="utf-8") as new_file:
                new_file.write(content)
            print(f"\nSuccess!\nSaved to {new_filename}")
        else:
            poison_epub(filename, mode, poison_class)
    except Exception as e:
        print("\nUh oh! Something went wrong.")
        print(e)

input("Press Enter to close window")