# Documents

## Layout

| Directory | Contents |
|---|---|
| `paper/` | KES 2026 paper source, its bibliography, and the Elsevier class files it needs |
| | `KES2026.pdf` is the file submitted to the conference. Do not regenerate it. |
| `slides/` | KES 2026 conference deck (source + build) and the dissertation defence deck |
| `figures/` | Images shared by the paper and the deck |
| `design/` | Editable diagram sources and development notes; nothing here is a deliverable |
| `reference/` | `KES26-model.pdf`, the layout the conference deck was modelled on |

## Building

Both documents resolve images through `\graphicspath{{../figures/}}`, so run each
from its own directory:

    cd docs/paper  && pdflatex PROCS_KES2026.tex   # run twice, plus bibtex

A build writes `PROCS_KES2026.pdf`, which is git-ignored. The submitted
`KES2026.pdf` is a separate filename and is never overwritten by a rebuild.
    cd docs/slides && pdflatex KES26-Radu.tex      # run twice, for the frame counter

`elsarticle.cls`, `ecrc.sty`, `framed.sty`, `Procs.pdf` and the two logo PDFs in
`paper/` ship with the Elsevier Procedia template and must stay beside the source:
some TeX engines (tectonic among them) ignore `TEXINPUTS`, so a separate template
directory does not resolve.
