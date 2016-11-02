# read-font

This is a Python script that converts character representations in various fonts (such as TrueType (.ttf) fonts) to JSON format. The data in the JSON file can then be used to build bitmapped (fixed size) fonts. One practical use for this is to construct bitmapped fonts that can be easily displayed on graphical LCDs connected to a microcontroller that doesn't have enough resources to display TrueType fonts directly.

The code is based on [this excellent article](https://dbader.org/blog/monochrome-font-rendering-with-freetype-and-python) by Dan Bader and on [his code](https://gist.github.com/dbader/5488053).

## Installation

- `pip install read-font` to download and install the version uploaded to PyPI.
- clone this repository and then run `python setup.py install` to install the latest version on github.

This should be enough in Linux. For Windows, you'll probably need to install the Freetype library:

- if your Python is 32-bit, you can install the Freetype library from [GnuWin32](http://gnuwin32.sourceforge.net/packages/freetype.htm).
- if your Python is 64-bit, you need to compile Freetype yourself, or look for a pre-built 64-bit Freetype DLL. A pre-built DLL that worked for me can be found [here](https://github.com/rougier/freetype-py/issues/17#issuecomment-195925807).

## Usage

The script needs a path to a font file (specified with the `-f` argument), a size for the font (specified with the `-s` argument) and a list of characters to process. The list can be specified either by:

- a range of ASCII codes using the `-r` option (for example, `-r 48,57` will process all digits from 0 to 9).
- an explicit list of characters using the `-c` option (for example, `-c "0123456789"` will process all digits from 0 to 9). `-c` can be given multiple times on the command line.

To output the data read from the font to a JSON file, use `-o <name_of_json_file>`.

`-v` enables verbose operation.

`--display-chars` enables verbose operation and also outputs the character bitmaps on the screen.

Example:

```
>read-font -f c:\Windows\fonts\couri.ttf -s 24 -c "A" --display-chars -o data.json
Char: 'A' Code: 65 Width: 14 Height: 14 Top: 14
......*****...
.........**...
........*.*...
........*.*...
.......*...*..
......*....*..
......*....*..
.....*.....*..
.....*******..
....*......*..
....*.......*.
...*........*.
...*........*.
*****....*****

Min height:14  Max height: 14
Min width: 14  Max width:  14
Wrote char data to 'data.json'
```

`data.json` looks like this:

```
[
    {
        "char": "A",
        "width": 14,
        "top": 14,
        "data": [
            "......*****...",
            ".........**...",
            "........*.*...",
            "........*.*...",
            ".......*...*..",
            "......*....*..",
            "......*....*..",
            ".....*.....*..",
            ".....*******..",
            "....*......*..",
            "....*.......*.",
            "...*........*.",
            "...*........*.",
            "*****....*****"
        ],
        "height": 14
    }
]
```

Most fields should be self-explanatory. `top` is the vertical distance from the character's baseline to its first displayed line, check [Dan's original article](https://dbader.org/blog/monochrome-font-rendering-with-freetype-and-python) for more details.

## Limitations

The script is alpha quality.

Works only with ASCII characters (codes from 0 to 127), not Unicode.

## License

`read-font` is licensed under the MIT license, like the original code from Dan Bader.

