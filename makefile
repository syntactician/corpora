M := -f texminted
S := -shell-escape

B := bibtex
L := pdflatex $S
P := python3
T := ptangle
W := pweave $M

NAME := fanfiction
SRC  := $(NAME).mdw
TEX  := $(NAME).tex
DOC  := $(NAME).pdf
PY   := $(NAME).py

all:
	@echo "You know not what you do."

sweep:
	@rm -rf              \
		*.aux        \
		*.fff        \
		*.log        \
		*.out        \
		__pycache__  \
		_minted*/    \
		matplotlibrc

clean: sweep
	@rm -f *.pdf

destroy: clean
	@rm -f *.jl *.py

weave:
	@echo 'figure.autolayout : True' > matplotlibrc
	# @ptangle fanfiction.mdw && python3 fanfiction.py
	@$W $(SRC)
	@sed -i -e '/minted/s/\%s/python/' $(TEX)
	@$L $(NAME)
	@$S $(NAME)
	@$L $(NAME)
	@$(MAKE) sweep

tex:
	@$L $(NAME)
	@$B $(NAME)
	@$B $(NAME)
	@$L $(NAME)
	@$L $(NAME)
	@$(MAKE) sweep

tangle:
	@$T $(SRC)

run: tangle
	@$P $(PY)
