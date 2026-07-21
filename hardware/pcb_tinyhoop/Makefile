# STRATOS TINYHOOP AIO — regenerate everything from scripts/design.py
# board/fab/check need KiCad python (pcbnew) + kicad-cli on PATH (the CI job
# runs them in the kicad/kicad:8.0 container); pinmap/schematic are pure python.
PY ?= python3

.PHONY: all board pinmap schematic fab check clean preview

all: board pinmap fab check

board:            ## generate stratos_tinyhoop_aio.kicad_pcb from design.py  (needs pcbnew)
	$(PY) scripts/gen_pcb.py

pinmap:           ## regen firmware board_pinmap_tinyhoop.h (real fw header)  (pure python)
	$(PY) scripts/gen_pinmap.py

schematic:        ## regenerate stratos_tinyhoop_aio.kicad_sch               (pure python)
	$(PY) scripts/gen_schematic.py

fab: board        ## export JLCPCB bom.csv, cpl.csv, gerbers            (needs pcbnew+kicad-cli)
	$(PY) scripts/export_fab.py

check: board pinmap  ## verify board nets + pinmap match design.py      (needs pcbnew)
	$(PY) scripts/check_consistency.py

preview: board    ## export top/bottom SVG previews                     (needs kicad-cli)
	kicad-cli pcb export svg --page-size-mode 2 --layers "F.Cu,F.SilkS,F.Paste,Edge.Cuts" -o preview/top.svg stratos_tinyhoop_aio.kicad_pcb
	kicad-cli pcb export svg --page-size-mode 2 --mirror --layers "B.Cu,B.SilkS,Edge.Cuts" -o preview/bottom.svg stratos_tinyhoop_aio.kicad_pcb

clean:
	rm -f jlcpcb/gerbers/* preview/*.svg
