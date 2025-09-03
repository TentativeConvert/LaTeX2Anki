# LaTeX2Anki

A small python script that uses [plastex](https://plastex.github.io/plastex/) to convert a LaTeX document consisting of structured notes into a csv file that can be imported into [Anki](https://apps.ankiweb.net/).

It's designed for the same use case as the older package [LaTeX-Note-Importer-for-Anki](https://github.com/TentativeConvert/LaTeX-Note-Importer-for-Anki/), by the same author, but aims to make better use of some of Anki's inbuilt features:

- cloze deletions
- dynamic page rendering based on screen size and user preferences (night mode)

Notes created and shared using LaTeX-Note-Importer are essentially static images.  Notes created and shared using the script and workflow described here are html based, with maths mixed in and rendered using Anki's inbuild MathJax engine.  


## Prerequisites

1. LaTeX

   (Strictly speaking, this is optional, but why would you be here if you didn't have LaTeX installed?)

2. Python

   You need `python 3`.  Clone this repository and run and several packages, in particular `plastex` and `beautifulsoup4`.  
   ``` bash
   pip3 install latex2anki
   ``` 

   This should automatically install the python packages `plastex` and `beautifulsoup4`.

3. Anki

   In Anki, you will once need to import the deck `example/example.apkg` so that the note type `MathCloze` becomes available in Anki. 
   You can immediately delete the deck again after importing it.

## Workflow

I describe the workflow here using the file `example.tex`.

0. Copy or symlink the files `latex2anki.sty` and `latex2anki.ini` into the directory in which your tex file `example.tex` lives.  

   You only need to do this once for each directory in which you want to keep your texed notes.

1. optional: Compile `example.tex` to `example.pdf` with LaTeX.

   Check that the pdf file looks as expected.
  
2. Run `latex2anki.py example.tex`.

   You need to call this command in the folder in which `example.tex` lives.
   
   It first converts the tex file to `example/example.html` via `plastex`, which you can view in your browser.
   In this step, all user defined macros get expanded, so that the html file only contains standard LaTeX commands.
   
   In a second step, the script converts the html file to `example/example.csv`.
      
3. Import `example/example.csv` into Anki.

   In the dialog window, choose:

   - update existing notes
   - note type: `MathCloze`
   
## Known issues, caveats & limitations

### Use `\(…\)` and `\[…\]` only for maths
  
Do not use `$…$` or `$$…$$` or `\begin{equation} … \end{equation}` etc. 

    
### Use `def` instead of `\renewcommand` to overwrite inbuilt commands
LaTeX's `\newcommand` works, and `renewcommand` mostly works, except for inbuilt commands.
For inbuilt commands, plastex ignores `\renewcommand`, see [plastex:issue#90](https://github.com/plastex/plastex/issues/90).
        
Workaround:  use `\def` to overwrite inbuilt commands, e.g.

``` latex
\def\vec #1{\mathbf{#1}}`
```
to redefine `\vec`.  Don't put  a space between  `…#1` and `{…`!

### Don't use `alignedat` environment
The `alignedat` environment appears to break plastex.
The `aligned` environment works.

### Empty lines in certain environments are lost.
For exmple, empty lines produced with 

``` latex
\\
\\  
```
    in an `aligned` environment are lost when processing with plastex.
Workaround:
``` latex
\\~
\\
```

### MathJax only includes certain packages out-of-the-box
 
See  [MathJax 3 documentation](https://docs.mathjax.org/en/v3.0/input/tex/extensions/ams.html ) for a list. (The list of MathJax 4 looks similar.  See [Anki:issue4277](https://github.com/ankitects/anki/issues/4277) for updates on the inclusion of MathJax 4 into Anki.)


## Design choices
   
### `note` environment and `field` command

The structure of `note` environment and `field` command is supposed to be reminiscent of the structure of `itemize` environment and `item` argument.  So it should feel sufficiently “LaTeXy”.  On the other hand, simply “itemizing” all field entries is very close to the internal logic of Anki, and it certainly accurately reflects the structure of the csv-file that is used as an intermediary to import notes form LaTeX into Anki.
 
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

There are two possible approaches to rendering an html-latex mix in Anki.

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

`plastex` mostly caters for option 1, so this is the path we follow here.  One exception is `tikz-cd` diagrams, which `plastex` converts to `svg`s.  My current inclination is to simply avoid such diagrams, so that we don't end up having to deal with the worst of both words 1 & 2.  If I really need a card with a diagram, perhaps  [amscd](https://docs.mathjax.org/en/latest/input/tex/extensions/amscd.html) would work instead.

It should be possible to set up `plastex` use option 2 for all maths, i.e. to turn all maths into images. But this is difficult to set up.  See [plastex:issue163](https://github.com/plastex/plastex/issues/163).
