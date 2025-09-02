# LaTeX2Anki

A small python script that uses [plastex](https://plastex.github.io/plastex/) to convert a LaTeX document consisting of structured notes into a csv file that can be imported into [Anki](https://apps.ankiweb.net/).

## Prerequisites

1. Python
You need `python 3` and several packages, in particular:
    
```bash
pip3 install plastex beautifulsoup4
``` 

2. Anki
In Anki, you will once need to import the empty deck file provided [TODO] so that the note type `MathCloze` becomes available.

## Workflow

1. (optional) LaTeX compilation
2. run `python3 latex2anki.py example.tex`
3. import `example/example.csv` into Anki

   - choose to update existing notes
   - note type: `MathCloze`
   
4. in case you are using tikz-cd diagrams, copy folder `images` from `example` to Anki's media folder, e.g. to
   ```bash
   …/snap/anki-desktop/common/Benutzer 1/collection.media
   ```
   
## Known issues & limitations
    
### MathJax only includes certain packages out-of-the-box
 
See  [MathJax 3 documentation](https://docs.mathjax.org/en/v3.0/input/tex/extensions/ams.html ) for a list. (The list of MathJax 4 looks similar.  See [Anki:issue4277](https://github.com/ankitects/anki/issues/4277) for updates on the inclusion of MathJax 4 into Anki.)
        
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
   
### Offline svg-images versus client-side MathJax rendering

Plastex treats maths in two different ways:

1. Most maths is included as plain latex in the html document, and displayed using MathJax.

   Pros:
    - (+) Can use clozes inside maths.  
    - (+) Exporting is easy.
    - (+) Supports nightmode coloring via css.
    
    Cons:
    - (-) Only displays with internet connection.
    - (-) Color highlighting of clozes *within* equations not supported.
    
2. `tikz-cd` diagrams are converted to `svg`'s.

    Pros: 
    - (+) Can be viewed offline.
    - (+) Supports nightmode colouring: can invert image via css
    
    Cons:  
    - (-) Exporting to Anki requires additional step: need to manually copy the `svg` files to Anki's media folder.
    - (-) Cannot included clozes within diagrams.     

Each way has pro's and con's.  Using both simultaneously gives us to the worst of both worlds.  Can this be avoided?
  
Option A: There should be a way to turn all maths into images.  But this is difficult to set up.  See
  [plastex:issue163](https://github.com/plastex/plastex/issues/163).
  
Option B: Can't MathJax compile tikz-cd directly?  Maybe need to use [amscd](https://docs.mathjax.org/en/latest/input/tex/extensions/amscd.html) instead.

