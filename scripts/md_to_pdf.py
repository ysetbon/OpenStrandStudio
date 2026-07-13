"""Convert a Markdown document (with images) to PDF using Qt.

Usage:
    python scripts\\md_to_pdf.py                          # converts the CP-drag issue doc
    python scripts\\md_to_pdf.py path\\to\\doc.md          # -> path\\to\\doc.pdf
    python scripts\\md_to_pdf.py doc.md -o out.pdf

Relative image paths inside the markdown are resolved against the .md file's
folder. If the target PDF is open in a viewer (locked), the result is written
next to it with a .new.pdf suffix instead of failing.
"""

import argparse
import os
import sys

DEFAULT_MD = os.path.normpath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "src", "documentation", "cp_drag_visibility_issue.md"))


def _die(msg):
    print("ERROR:", msg)
    sys.exit(1)


def _import_qt():
    try:
        from PyQt5.QtCore import QUrl, QMarginsF
        from PyQt5.QtGui import QTextDocument, QPageLayout, QPageSize
        from PyQt5.QtWidgets import QApplication
    except ImportError as exc:
        _die("PyQt5 is not available in this Python environment (%s).\n"
             "Run with the interpreter you use for the app, or: pip install PyQt5"
             % exc)
    try:
        from PyQt5.QtPrintSupport import QPrinter
    except ImportError as exc:
        _die("PyQt5.QtPrintSupport is missing (%s).\n"
             "Reinstall PyQt5 (pip install --force-reinstall PyQt5); the print "
             "module ships with the standard PyQt5 wheel." % exc)
    return (QUrl, QMarginsF, QTextDocument, QPageLayout, QPageSize,
            QApplication, QPrinter)


def convert(md_path, pdf_path):
    (QUrl, QMarginsF, QTextDocument, QPageLayout, QPageSize,
     QApplication, QPrinter) = _import_qt()

    # Do NOT use the offscreen platform here: it has no system fonts on
    # Windows, which silently produces a PDF with no visible text.
    app = QApplication.instance() or QApplication([sys.argv[0]])

    with open(md_path, "r", encoding="utf-8") as f:
        text = f.read()

    doc = QTextDocument()
    # Resolve relative image paths against the markdown file's folder
    doc.setMetaInformation(
        QTextDocument.DocumentUrl,
        QUrl.fromLocalFile(os.path.dirname(os.path.abspath(md_path)) + os.sep).toString())
    if hasattr(doc, "setMarkdown"):
        doc.setMarkdown(text)
    else:  # Qt < 5.14 fallback
        try:
            import markdown
        except ImportError:
            _die("This Qt build has no QTextDocument.setMarkdown and the "
                 "'markdown' package is not installed.\n"
                 "Either upgrade PyQt5 (>= 5.14) or: pip install markdown")
        doc.setHtml(markdown.markdown(text, extensions=["tables", "fenced_code"]))

    # Write to a temp file first so a viewer holding the target open
    # cannot make us silently produce nothing.
    tmp_path = pdf_path + ".part"
    printer = QPrinter(QPrinter.HighResolution)
    printer.setOutputFormat(QPrinter.PdfFormat)
    printer.setOutputFileName(tmp_path)
    printer.setPageLayout(QPageLayout(
        QPageSize(QPageSize.A4), QPageLayout.Portrait,
        QMarginsF(15, 15, 15, 15), QPageLayout.Millimeter))

    page = printer.pageRect(QPrinter.Point)
    doc.setPageSize(page.size())
    doc.setTextWidth(page.width())
    doc.print_(printer)

    if not os.path.exists(tmp_path) or os.path.getsize(tmp_path) == 0:
        _die("PDF rendering produced no output (QPrinter failed).")

    try:
        os.replace(tmp_path, pdf_path)
        return pdf_path
    except PermissionError:
        alt = os.path.splitext(pdf_path)[0] + ".new.pdf"
        os.replace(tmp_path, alt)
        print("NOTE: %s is open in a viewer and locked." % os.path.basename(pdf_path))
        print("      The fresh PDF was saved as: %s" % alt)
        return alt


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("markdown", nargs="?", default=DEFAULT_MD,
                        help="input .md file (default: the CP-drag issue doc)")
    parser.add_argument("-o", "--output",
                        help="output .pdf path (default: input name with .pdf)")
    args = parser.parse_args()

    md_path = os.path.abspath(args.markdown)
    if not os.path.isfile(md_path):
        _die("markdown file not found: %s" % md_path)
    pdf_path = os.path.abspath(args.output) if args.output \
        else os.path.splitext(md_path)[0] + ".pdf"

    result = convert(md_path, pdf_path)
    print("wrote", result)


if __name__ == "__main__":
    main()
