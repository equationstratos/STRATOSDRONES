# STRATOSDRONE PCB — regenerate everything from design.py
# Requires KiCad 7 python (pcbnew) + kicad-cli on PATH.
PY ?= python3

.PHONY: all board pinmap fab check clean preview

all: board pinmap fab check

board:            ## generate stratosdrone.kicad_pcb from design.py
	$(PY) scripts/gen_pcb.py

pinmap:           ## regenerate firmware board_pinmap.h
	$(PY) scripts/gen_pinmap.py

fab: board        ## export JLCPCB bom.csv, cpl.csv, gerbers
	$(PY) scripts/export_fab.py

check: board pinmap  ## verify board nets + pinmap match design.py
	$(PY) scripts/check_consistency.py

preview: board    ## export top/bottom SVG previews
	kicad-cli pcb export svg --page-size-mode 2 --layers "F.Cu,F.SilkS,F.Paste,Edge.Cuts" -o preview/top.svg stratosdrone.kicad_pcb
	kicad-cli pcb export svg --page-size-mode 2 --mirror --layers "B.Cu,B.SilkS,Edge.Cuts" -o preview/bottom.svg stratosdrone.kicad_pcb

clean:
	rm -f jlcpcb/gerbers/* preview/*.svg
