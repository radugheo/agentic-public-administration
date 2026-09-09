# Documents

## Layout

| Directory | Contents |
|---|---|
| `paper/` | KES 2026 paper: source, bibliography, compiled PDF, and the Elsevier class files it needs |
| `slides/` | KES 2026 conference deck (source + PDF), and an earlier presentation of the same work |
| `figures/` | Images shared by the paper and the deck |
| `design/` | Editable diagram sources and working notes |
| `reference/` | `KES26-model.pdf`, the layout the conference deck follows |

## Building

Both documents resolve images through `\graphicspath{{../figures/}}`, so run each
from its own directory:

    cd docs/paper  && pdflatex PROCS_KES2026.tex   # run twice, plus bibtex
    cd docs/slides && pdflatex KES26-Radu.tex      # run twice, for the frame counter

`elsarticle.cls`, `ecrc.sty`, `framed.sty`, `Procs.pdf` and the two logo PDFs in
`paper/` ship with the Elsevier Procedia template and must stay beside the source:
some TeX engines (tectonic among them) ignore `TEXINPUTS`, so a separate template
directory does not resolve.
