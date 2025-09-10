# LaTeX2Anki

A small python script that uses [plastex](https://plastex.github.io/plastex/) to convert a LaTeX document consisting of structured notes into a csv file that can be imported into [Anki](https://apps.ankiweb.net/).

It's designed for the same use case as the older package [LaTeX-Note-Importer-for-Anki](https://github.com/TentativeConvert/LaTeX-Note-Importer-for-Anki/), by the same author, but aims to make better use of some of Anki's inbuilt features:

- cloze deletions
- dynamic page rendering based on screen size and user preferences (night mode)

Notes created and shared using LaTeX-Note-Importer are essentially static images.  Notes created and shared using the script and workflow described here are html based, with maths mixed in and rendered using Anki's built-in MathJax engine.  


## Prerequisites

1. LaTeX

   (Strictly speaking, this is optional, but why would you be here if you didn't have LaTeX installed?)

2. Python

   You need `python 3` and several packages, including recent versions of `pip`, `setuptools` and `wheels`.  You can see which versions you have with 
   ```
   python3 -m pip show wheel pip setuptools
   ```
   and update if necessary with 
   ```
   python -m pip install --upgrade pip setuptools wheel
   ```
   The installation process for `anki2latex` described in the next step works for me with the following versions of the above packages:
   ```
   pip 25.0.1
   setuptools 45.2.0
   wheel 0.34.2
   ```
3. anki2latex

   Clone this repository into some local folder and run
   ``` bash
   pip install .
   ``` 
   in that folder (the folder containing `pyproject.toml`).    This should automatically install the python packages `plastex` (version ≥ 3.1) and `beautifulsoup4`.   (In case you want to do local development on this    python script, use  `pip install --editable .` instead, so you do not need to reinstall after each edit.  If the installation of `anki2latex` fails, you might still be able to use the script by calling it directly, see Step 2 of [Workflow](#Workflow) below.)
     
4. Anki

   In Anki, you will once need to import the deck `example/example.apkg` so that the note type `MathCloze` becomes available in Anki.  (Hopefully, this will also install the necessary fonts for MathCloze in Anki -- I need to test this. Exporting `example.apkg` with the option `export media` did lead to a larger file than exporting without this option, so hopefully this difference is caused precisely by the fonts.)
   
   You can immediately delete the deck again after importing it.

## Workflow

I describe the workflow here using the file `example.tex`.

0. Copy or symlink the files `latex2anki.sty` and `latex2anki.ini` into the directory in which your tex file `example.tex` lives.  

   You only need to do this once for each directory in which you want to keep your texed notes.

1. optional: Compile `example.tex` to `example.pdf` with LaTeX.

   Check that the pdf file looks as expected.  
   
   *Details:* The layout of the pdf file is controlled by (the `\if\plastex\else`-branches of) the LaTeX package `latex2anki.sty`, which should be in the same folder as the tex file.  This LaTeX package is specifically designed for the Anki note template `MathCloze`.  If you use a different template, you will need to adapt this file.
  
2. Run `latex2anki example.tex`.

   You need to call this command in the folder in which `example.tex` lives.   This script does two things.  In a first step, `plastex` is called to convert the tex file to `example/example.html`, which you can view in your browser.  In a second step, the script converts the html file to `example/example.csv`.

   *Aside:* If the installation of `latex2anki` described in Step 2 of [Prerequisites](#Prerequisites) fails, you might still be able to run `latex2anki` by calling
   ``` bash
   python3 latex2anki/cli.py example.tex
   ```
   
   *Details:* The main code of `latex2anki` is contained in `latex2anki/cli.py`. 
   
   The first conversion step (`tex > html`) is delegated to `plastex`.  The details of this conversion are controlled by three files: by  (the `\if\plastex`-branches of) `latex2anki.sty` and `latex2anki.ini`, which should both be in the same folder as the tex file, and a temporary template file created on the fly by the script itself (see constant `JINJA_TEMPLATE_FOR_PLASTEX` defined at the top of `latex2anki/cli.py`).  Note that `plastex` automatically expands all user-defined macros, so that the html file only contains standard LaTeX commands.  The appearance of `example.html` in the browser is controlled by the file `example/styles/theme-white.css`, which is copied there by plastex from the resources that get installed with plastex.  It will necessarily look very different from the final cards in Anki, but at least you can check whether your equations render at all.
   
   For details of the second conversion step (`html > csv`), see the code in `cli.py`.
         
3. Import `example/example.csv` into Anki.

   In the dialog window, choose:

   - update existing notes
   - note type: `MathCloze`
   
For a more elaborate example of what a tex file with notes might look like, see [LinACards2025.tex](https://github.com/TentativeConvert/LinACards2025/blob/main/LinACards2025.tex).


## Known issues, caveats & limitations

### Use `\(…\)` and `\[…\]` only for maths
  
Do not use `$…$` or `$$…$$` or `\begin{equation} … \end{equation}` etc. 

### Don't nest maths within `\text{…}` within maths

It seems that at some stage of the conversion process, `\(\text{\(x\)}\)` gets converted into `\(\text{$x$}\)`, which then displays incorrectly.  It looks like a `plastex` bug to me, but I have not investigated details.

### Avoid clozes within maths

While clozes within maths work in principal, they do tend to break things.  

One of the things that definitely does not work for clozes within maths is colour-highlighting.
By default, Anki highlights the revealed cloze deletions in blue.  This works for maths contained within clozes, e.g. `the answer is \cloze{1}\(b^2 + c^2\)\clend`.  But it does *not* work for clozes within maths, e.g. `the answer is \(a^2 = \cloze{1} b^2 + c^2\clend\)`.  You could write `the answer is \(a^2 = \)\cloze{1}\(b^2 + c^2\)\clend` instead, and then everything will look as expected again.  

Note that this is a limitation of Anki/MathJax, not a limitation of the conversion process.

### Use `def` instead of `\renewcommand` to overwrite inbuilt commands
LaTeX's `\newcommand` works, and `\renewcommand` mostly works, except for inbuilt commands.
For inbuilt commands, plastex ignores `\renewcommand`, see [plastex:issue#90](https://github.com/plastex/plastex/issues/90).
        
Workaround:  use `\def` to overwrite inbuilt commands, e.g.

``` latex
\def\vec #1{\mathbf{#1}}
```
to redefine `\vec`.  Don't put  a space between  `…#1` and `{…`!

### Don't use `alignedat` environment
The `alignedat` environment appears to break plastex.
The `aligned` environment works.

### Use `\\~` instead of `\\` to produce empty lines in certain environments
For exmple, empty lines produced with 

``` latex
\\
\\  
```
in an `aligned` environment are lost when processing with plastex.  Using `\\~` instead of `\\` provides a simple workaround.

### Don't use `\slash`

It appears that plastex does not render `\slash`.

### Don't write anything below `\end{document}`

It appears that plastex does not stop parsing at  `\end{document}`, and thus easily gets confused if the file continues past this point.  I have not investigated details.

### Enclose lists and enumerations in `\begin{center}…\end{center}`

You won't get any errors if you don't, but the cards in Anki will look much nicer on large screens if you do.

### If you enclose prose in `\begin{center}…\end{center}`, add `\par`

That is, write your paragraph as follows:

``` latex
\begin{center}
\par This is some nice text.
\end{center}
```
Otherwise, each word will appear on a new line in Anki.  (The center environment is converted to a `<div class="centered">` environment by plastex, which is styled with the css attributes `display:flex` and `flex-direction:column` in the MathCloze card template.  These css attributes are often what we want, e.g. when the center environment contains a list, but for pure it results in each word being placed on a new line.  If we add `\par` in the tex file, the converted text gets wrapped in a <p> environment, and the problem disappears.


### MathJax only includes certain packages out-of-the-box
 
See  [MathJax 3 documentation](https://docs.mathjax.org/en/v3.0/input/tex/extensions/ams.html ) for a list. (The list of MathJax 4 looks similar.  See [Anki:issue4277](https://github.com/ankitects/anki/issues/4277) for updates on the inclusion of MathJax 4 into Anki.)

## Design choices
   
### `note` environment and `field` command

The structure of `note` environment and `field` command is supposed to be reminiscent of the structure of `itemize` environment and `item` argument.  So it should feel sufficiently “LaTeXy”.  On the other hand, simply “itemizing” all field entries is very close to the internal logic of Anki, and it certainly accurately reflects the structure of the csv file that is used as an intermediary to import notes form LaTeX into Anki.
 
### `cloze`, `hint` and `clend` commands

It's tempting to implement clozes as a command with one mandatory argument (the cloze text) and one optional argument (the hint), e.g.

``` latex
\cloze[a hint]{the hidden text}
```
That would make it possible (or at least much easier) to produce a nice html preview of the notes via plastex. 

However, using three different commands offers maximal flexibilty.
Note that for notes that are generated live within Anki via MathJax, the only question that should matter is whether both the note with the cloze and the note with the hint are compilable.  For example:

``` latex
\begin{tabular}{cc}
 a {{c1:: & b \\
 c }}    & d 
 \end{tabular}
```
and 

``` latex
\(a + {{c1:: b\) and \(c + }} d\)
```
are both completely legitimate in Anki, but it would not be possible to generated these examples with a syntax of the form `\cloze[a hint]{the hidden text}`
   
### MathJax rendering versus svg-images

There are two possible approaches to rendering an html-tex mix in Anki.

1. Include LaTeX directly within the html code, so that it is renedered with Anki's built-in MathJax engine.

   Pros & Cons:
    - ❌ Loading probably slower.
    - ✅ Can use clozes inside maths (but cloze-specific colour highlighting not supported).  
    - ✅ Importing is easy.
    -
    
2. Convert LaTeX to `svg`s, and include references to the svg files in the html code.

    Pros & Cons: 
    - ✅ Loading probably faster.
    - ❌ Importing into Anki requires additional step: need to manually copy the `svg` files to Anki's media folder
          (e.g. to   ` …/snap/anki-desktop/common/Benutzer 1/collection.media` if Anki is installed as a snap package).
    - ❌ Cannot included clozes within diagrams.     


In both options, the cards can be viewed offline, and both options support nightmode colouring via css (colour of images can be inverted via css).

`plastex` mostly caters for option 1, so this is the path we follow here.  One exception is `tikz-cd` diagrams, which `plastex` converts to `svg`s.  My current inclination is to simply avoid such diagrams, so that we don't end up having to deal with the worst of both worlds 1 & 2.  If I really need a card with a diagram, perhaps  [amscd](https://docs.mathjax.org/en/latest/input/tex/extensions/amscd.html) would work instead.

It should be possible to set up `plastex` to use option 2 for all maths, i.e. to turn all maths into images. But this is difficult to set up.  See [plastex:issue163](https://github.com/plastex/plastex/issues/163).
