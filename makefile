Q := -quiet
R := -r ~/courses/latexmkrc
S := -shell-escape
T := -f texminted

L := latexmk $Q $R
P := pdflatex $S
W := pweave $T

all: erotica

sweep:
	@$L -c
	@rm -rf *.fff matplotlibrc _minted*/ figures/

clean: sweep
	@$L -C

erotica:
	# @echo 'figure.autolayout : True' > matplotlibrc
	# @ptangle erotica.mdw && python erotica.py
	@$W erotica.mdw
	@$P erotica
	@$P erotica
	@$(MAKE) sweep
