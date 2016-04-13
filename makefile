Q := -quiet
R := -r ~/courses/latexmkrc
S := -shell-escape
T := -f texminted

L := latexmk $Q $R
P := pdflatex $S
W := pweave $T

all: fanfiction

sweep:
	@$L -c
	@rm -rf *.fff matplotlibrc _minted*/ figures/

clean: sweep
	@$L -C

fanfiction:
	# @echo 'figure.autolayout : True' > matplotlibrc
	# @ptangle fanfiction.mdw && python3 fanfiction.py
	@$W fanfiction.mdw
	@sed -i -e '/minted/s/\%s/python/' fanfiction.tex
	@$P fanfiction
	@$P fanfiction
	@$(MAKE) sweep
