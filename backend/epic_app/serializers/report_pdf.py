from datetime import datetime
from io import BytesIO
from typing import Any, List, Optional

from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.shapes import Drawing
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.styles import ParagraphStyle as PS
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm, inch
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer
from reportlab.platypus.doctemplate import BaseDocTemplate, PageTemplate
from reportlab.platypus.frames import Frame
from reportlab.platypus.paragraph import Paragraph
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.rl_config import defaultPageSize

PAGE_HEIGHT = defaultPageSize[1]
PAGE_WIDTH = defaultPageSize[0]


class EpicStyles:
    h1 = PS(
        fontName="Times-Bold",
        fontSize=14,
        name="TOCHeading1",
        leftIndent=20,
        firstLineIndent=-20,
        spaceBefore=5,
        leading=16,
    )
    h2 = PS(
        fontSize=12,
        name="TOCHeading2",
        leftIndent=40,
        firstLineIndent=-20,
        spaceBefore=0,
        leading=12,
    )
    h3 = PS(
        fontSize=10,
        name="TOCHeading3",
        leftIndent=60,
        firstLineIndent=-20,
        spaceBefore=0,
        leading=12,
    )
    h4 = PS(
        fontSize=10,
        name="TOCHeading4",
        leftIndent=100,
        firstLineIndent=-20,
        spaceBefore=0,
        leading=12,
    )


class EpicReportDocTemplate(SimpleDocTemplate):
    def afterFlowable(self, flowable):
        """
        Registers TOC entries.
        """
        if flowable.__class__.__name__ == "Paragraph":
            indentation = {
                "TOCHeading1": 1,
                "TOCHeading2": 2,
                "TOCHeading3": 3,
                "TOCHeading4": 4,
            }
            level = indentation.get(flowable.style.name, None)
            if level:
                self.notify("TOCEntry", (level, flowable.getPlainText(), self.page))


class EpicPdfReport:
    styles = getSampleStyleSheet()
    report_title = "Epic Report"
    report_subtitle = ""
    report_author = ""
    report_description = "An automatic generated report containing all the questions and answers taken by the users of the organization."

    # Create the PDF object, using the buffer as its "file."
    def _init_abstract(self):
        intro = (
            f"{self.report_description} <br />"
            f"<b>Report requested by:</b> {self.report_author}.<br />"
            f"<b>Report generated on:</b> {datetime.now()} using the python library 'ReportLab'."
        )
        self._flowables.append(PageBreak())
        self._append_line("Abstract", EpicStyles.h1)
        self._append_line(intro)

    def _init_toc(self):
        # TODO: clickable TOC https://www.reportlab.com/snippets/13/
        self._flowables.append(PageBreak())
        self._toc = TableOfContents()
        self._toc.levelStyles = [
            EpicStyles.h1,
            EpicStyles.h2,
            EpicStyles.h3,
            EpicStyles.h4,
        ]
        self._flowables.append(self._toc)
        self._flowables.append(PageBreak())

    def _first_page(self, canvas, doc):
        subject = (
            self.report_subtitle + "\n" + self.report_description
            if self.report_subtitle
            else self.report_subtitle
        )
        canvas.saveState()
        canvas.setFont("Times-Bold", 64)
        canvas.drawCentredString(
            PAGE_WIDTH / 2.0, 2 * PAGE_HEIGHT / 3, self.report_title
        )
        if self.report_subtitle:
            canvas.setFont("Times-Bold", 16)
            canvas.drawCentredString(
                PAGE_WIDTH / 2.0, (PAGE_HEIGHT / 3), self.report_subtitle
            )

        # Set additional information.
        canvas.setAuthor(self.report_author)
        canvas.setTitle(self.report_title)

        canvas.setSubject(subject)
        canvas.restoreState()

    def _later_pages(self, canvas, doc):
        canvas.saveState()
        canvas.setFont("Times-Roman", 9)
        canvas.drawString(
            inch, 0.75 * inch, "Page %d %s" % (doc.page, self.report_title)
        )
        canvas.restoreState()

    def _append_charts(self, input_data: dict):
        drawing = Drawing(400, 200)
        id_keys = [id_k for id_k in input_data.keys() if not "_justify" in str(id_k)]
        if not id_keys:
            return
        id_values = [input_data[id_k] for id_k in id_keys]

        bc = VerticalBarChart()
        bc.x = 50
        bc.y = 50
        bc.height = 125
        bc.width = 300
        bc.data = [id_values]
        # bc.strokeColor = colors.black
        bc.valueAxis.valueMin = 0
        bc.valueAxis.valueMax = sum(id_values)
        bc.valueAxis.valueStep = 1
        #
        bc.categoryAxis.categoryNames = list(map(str, id_keys))
        bc.categoryAxis.labels.angle = 30
        bc.categoryAxis.labels.boxAnchor = "ne"
        bc.categoryAxis.labels.dx = 8
        bc.categoryAxis.labels.dy = -2
        drawing.add(bc)

        # Add to report.
        self._append_line("Answers:", EpicStyles.h3)
        self._flowables.append(drawing)

    def _append_line(self, line: str, style: Optional[Any] = None):
        if not style:
            style = self.styles["Normal"]
        self._flowables.append(Paragraph(line, style))
        self._flowables.append(Spacer(1, 0.2 * inch))

    def _append_justifications(self, q_qa: dict):
        q_summary = q_qa["summary"]
        self._append_line("Justifications:", EpicStyles.h3)
        for k_j in q_summary.keys():
            if "justify" not in str(k_j):
                continue
            j_line = "Justify {}:".format(str(k_j).split("_")[0])
            self._append_line(j_line)
            for line in q_summary[k_j]:
                self._append_line(line)

    def _append_questions(self, questions_data: dict):
        if not questions_data:
            self._append_line("No questions available.")
            return
        for q_entry in questions_data:
            self._append_line(q_entry["title"], EpicStyles.h2)
            if not q_entry["question_answers"]["answers"]:
                self._append_line("No recorded answers.")
                continue
            self._append_charts(q_entry["question_answers"]["summary"])
            self._append_justifications(q_entry["question_answers"])

    def _append_programs(self, report_data: dict):
        for p_entry in report_data:
            program_name = p_entry["name"]
            self._append_line(f"Program: {program_name}", EpicStyles.h1)
            self._append_questions(p_entry["questions"])
            self._flowables.append(PageBreak())

    def generate_report(self, buffer: BytesIO, report_data: dict):
        self._flowables = [Spacer(1, 2 * inch)]
        self._init_abstract()
        self._init_toc()
        self._append_programs(report_data)
        EpicReportDocTemplate(buffer).multiBuild(
            self._flowables,
            onFirstPage=self._first_page,
            onLaterPages=self._later_pages,
        )
