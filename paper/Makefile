build: clean main.pdf

main.pdf: main.tex res.bib
	pdflatex main.tex
	bibtex main
	pdflatex main.tex
	pdflatex main.tex

clean:
	rm -rf main.pdf main.out main.log main.aux main.bbl main.blg