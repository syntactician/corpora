M := -f texminted
S := -shell-escape

L := pdflatex $S
P := python3
T := ptangle
W := pweave $M

all: weave tangle

sweep:
	@rm -rf              \
		*.aux        \
		*.fff        \
		*.log        \
		*.out        \
		*.tex*       \
		_minted*/    \
		figures/     \
		matplotlibrc


clean: sweep
	@rm -f *.pdf

destroy: clean
	@rm -f *.jl *.py

weave:
	# @echo 'figure.autolayout : True' > matplotlibrc
	# @ptangle fanfiction.mdw && python3 fanfiction.py
	@$W fanfiction.mdw
	@sed -i -e '/minted/s/\%s/python/' fanfiction.tex
	@$L fanfiction
	@$L fanfiction
	@$(MAKE) sweep

tangle:
	@$T fanfiction.mdw

run: tangle
	@$P fanfiction.py
