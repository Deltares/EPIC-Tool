import abc

from django import forms
from django.contrib import admin
from django.shortcuts import redirect, render
from django.urls import path

from epic_app.importers.xlsx import (
    BaseEpicImporter,
    EpicAgencyImporter,
    EpicDomainImporter,
    EvolutionQuestionImporter,
    KeyAgencyActionsQuestionImporter,
    NationalFrameworkQuestionImporter,
)


class XlsxImportForm(forms.Form):
    """
    Simple form to allow importing a 'xlsx' file.

    Args:
        forms (forms.Form): Default Django form.
    """

    xlsx_file = forms.FileField()


class ImportEntityAdmin(admin.ModelAdmin):
    """
    Overriding of the Area list in the admin page so that we can add our custom import for all the data.
    """

    # Admin pages.
    change_list_template = "import_changelist.html"

    def get_urls(self):
        """
        Extends the default get_urls so we can inject the import-csv on

        Returns:
            List[str]: A list of the urls to load from the admin page.
        """
        urls = super().get_urls()
        my_urls = [
            path("import-xlsx/", self.import_xlsx),
        ]
        return my_urls + urls

    def import_xlsx(self, request):
        """
        Imports a csv file into the EPIC database structure.

        Args:
            request (HTTPRequest): HTML request.

        Returns:
            HTTPRequest: HTML response.
        """
        if request.method == "POST":
            try:
                self.get_importer().import_file(request.FILES["xlsx_file"])
                self.message_user(request, "Your xlsx file has been imported")
            except:
                self.message_user(
                    request, "It was not possible to import the requested xlsx file."
                )
            return redirect("..")

        form = XlsxImportForm()
        payload = {"form": form}
        return render(request, "admin/xlsx_form.html", payload)

    @abc.abstractmethod
    def get_importer(self) -> BaseEpicImporter:
        raise NotImplementedError("Should be implemented in concrete class.")


class AreaAdmin(ImportEntityAdmin):
    """
    Area admin page to allow CSV import.
    """

    def get_importer(self) -> EpicDomainImporter:
        return EpicDomainImporter()


class AgencyAdmin(ImportEntityAdmin):
    """
    Agency admin page to allow CSV import.
    """

    def get_importer(self) -> EpicAgencyImporter:
        return EpicAgencyImporter()


class NfqAdmin(ImportEntityAdmin):
    """
    National Framework Question admin page to allow CSV import.
    """

    def get_importer(self) -> NationalFrameworkQuestionImporter:
        return NationalFrameworkQuestionImporter()


class KaaAdmin(ImportEntityAdmin):
    """
    Key Agency Actions Question admin page to allow CSV import.
    """

    def get_importer(self) -> KeyAgencyActionsQuestionImporter:
        return KeyAgencyActionsQuestionImporter()


class EvoAdmin(ImportEntityAdmin):
    """
    Evolution Question admin page to allow CSV import.
    """

    def get_importer(self) -> EvolutionQuestionImporter:
        return EvolutionQuestionImporter()
