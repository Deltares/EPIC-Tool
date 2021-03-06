import csv
from pathlib import Path
from typing import List, Type, Union

from django.core.files.uploadedfile import InMemoryUploadedFile
from django.forms import ValidationError
from openpyxl.cell import Cell

from epic_app.importers.xlsx.base_importer import BaseEpicImporter
from epic_app.models.epic_questions import (
    EvolutionQuestion,
    KeyAgencyActionsQuestion,
    NationalFrameworkQuestion,
    Question,
)
from epic_app.models.models import Program


class _YesNoJustifyQuestionImporter(BaseEpicImporter):
    class XlsxLineObject(BaseEpicImporter.XlsxLineObject):
        group: str
        program: str
        title: str
        description: str

        @classmethod
        def from_xlsx_row(cls, xlsx_row: List[Cell]):
            new_obj = cls()
            new_obj.group = cls.get_valid_cell(xlsx_row, 0)
            new_obj.program = cls.get_valid_cell(xlsx_row, 1)
            new_obj.description = cls.get_valid_cell(xlsx_row, 2)
            new_obj.title = cls.get_valid_cell(xlsx_row, 3)
            return new_obj

    def import_file(self, input_file: Union[InMemoryUploadedFile, Path]):
        """
        Imports a 'XLSX file', because we only support one importer we can embed it here.

        Args:
            input_file (Union[InMemoryUploadedFile, Path]): File to be imported as a YNJustify question.
        """
        line_objects = self._get_xlsx_line_objects(input_file)
        # Skip the first line as it's the columns names
        _headers = line_objects.pop(0)
        self._cleanup_questions()
        errors_found = self._validate(line_objects)
        if any(errors_found):
            raise ValidationError(errors_found)

        self._import_questions(line_objects)

    def _get_type(self) -> Type[Question]:
        pass

    def _cleanup_questions(self):
        self._get_type().objects.all().delete()

    def _validate(
        self,
        xlsx_line_objects: List[XlsxLineObject],
    ) -> List[str]:
        errors_found = []
        n_line_addition = 2  # Excluded header + start enumerate is 0.
        for n_line, xlsx_line in enumerate(xlsx_line_objects):
            if not Program.objects.filter(
                name__iexact=xlsx_line.program, group__name__iexact=xlsx_line.group
            ).exists():
                error_line = n_line + n_line_addition
                errors_found.append(
                    f"  - Line {error_line}. Program: '{xlsx_line.program}', Group: '{xlsx_line.group}' does not exist."
                )
        return errors_found

    def _import_questions(self, imported_questions: List[XlsxLineObject]):
        for q_question in imported_questions:
            # Create new question
            f_program_query = Program.objects.get(
                name__iexact=q_question.program, group__name__iexact=q_question.group
            )
            c_question: Question = self._get_type()(
                title=q_question.title,
                description=q_question.description,
                program=f_program_query,
            )
            c_question.save()


class NationalFrameworkQuestionImporter(_YesNoJustifyQuestionImporter):
    def _get_type(self) -> Question:
        return NationalFrameworkQuestion


class KeyAgencyActionsQuestionImporter(_YesNoJustifyQuestionImporter):
    def _get_type(self) -> Question:
        return KeyAgencyActionsQuestion


class EvolutionQuestionImporter(BaseEpicImporter):
    class XlsxLineObject(BaseEpicImporter.XlsxLineObject):
        program: str
        dimension: str
        nascent_description: str
        engaged_description: str
        capable_description: str
        effective_description: str

        @classmethod
        def from_xlsx_row(cls, xlsx_row):
            new_line = cls()
            new_line.program = cls.get_valid_cell(xlsx_row, 1)
            dimension = cls.get_valid_cell(xlsx_row, 2)
            if not dimension:
                dimension = "Default dimension"
            new_line.dimension = dimension
            new_line.nascent_description = cls.get_valid_cell(xlsx_row, 3)
            new_line.engaged_description = cls.get_valid_cell(xlsx_row, 4)
            new_line.capable_description = cls.get_valid_cell(xlsx_row, 5)
            new_line.effective_description = cls.get_valid_cell(xlsx_row, 6)
            return new_line

    def _validate(
        self,
        xlsx_line_objects: List[XlsxLineObject],
    ) -> List[str]:
        errors_found = []
        n_line_addition = 2  # Excluded header + start enumerate is 0.
        for n_line, xlsx_line in enumerate(xlsx_line_objects):
            if not Program.objects.filter(name__iexact=xlsx_line.program).exists():
                error_line = n_line + n_line_addition
                errors_found.append(
                    f"  - Line {error_line}. Program: '{xlsx_line.program}' does not exist."
                )
        return errors_found

    def import_file(self, input_file: Union[InMemoryUploadedFile, Path]):
        line_objects = self._get_xlsx_line_objects(input_file)
        self._cleanup_questions()
        _headers = line_objects.pop(0)
        errors_found = self._validate(line_objects)
        if any(errors_found):
            raise ValidationError(errors_found)

        self._import_questions(line_objects)

    def _cleanup_questions(self):
        EvolutionQuestion.objects.all().delete()

    def _import_questions(self, imported_questions: List[XlsxLineObject]):
        for q_question in imported_questions:
            # Create new question
            p_found = Program.objects.get(name__iexact=q_question.program)
            c_question = EvolutionQuestion(
                title=q_question.dimension,
                nascent_description=q_question.nascent_description,
                engaged_description=q_question.engaged_description,
                capable_description=q_question.capable_description,
                effective_description=q_question.effective_description,
                program=p_found,
            )
            c_question.save()
