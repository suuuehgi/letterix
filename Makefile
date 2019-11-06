folder_minimal := "minimal"

minimal: minimal.tex
	mkdir -p $(folder_minimal)
	pdflatex -shell-escape --output-directory=$(folder_minimal) minimal.tex

clean:
	rm -r $(folder_minimal)
