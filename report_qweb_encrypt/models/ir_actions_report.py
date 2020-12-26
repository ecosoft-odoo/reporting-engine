# Copyright 2020 Creu Blanca
# Copyright 2020 Ecosoft Co., Ltd.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import time
import logging
from odoo import fields, models, _
from io import BytesIO
from odoo.tools.safe_eval import safe_eval
from odoo.exceptions import ValidationError


_logger = logging.getLogger(__name__)
try:
    from PyPDF2 import PdfFileReader, PdfFileWriter
except ImportError as err:
    _logger.debug(err)


class IrActionsReport(models.Model):

    _inherit = 'ir.actions.report'

    encrypt = fields.Selection(
        [("manual", "Manual Input Password"),
         ("auto", "Auto Generated Password")],
        string="Encryption",
        default="manual",
        help="* Manual Input: allow user to key in password on the fly, "
        "but available only on document print action.\n"
        "* Auto Generated: system will auto encrypt password when PDF created, "
        "based on provided python syntax."
    )
    encrypt_password = fields.Char(
        help="Python code syntax to gnerate password.",
    )

    def render_qweb_pdf(self, res_ids=None, data=None):
        document, ttype = super(IrActionsReport, self).render_qweb_pdf(
            res_ids=res_ids, data=data)
        password = self._get_pdf_password(res_ids[:1])
        document = self._encrypt_pdf(document, password)
        return document, ttype

    def _get_pdf_password(self, res_id):
        encrypt_password = False
        if self.encrypt == "manual":
            pass  # for manual case, encryption will be done by report_download()
        elif self.encrypt == "auto" and self.encrypt_password:
            obj = self.env[self.model].browse(res_id)
            try:
                encrypt_password = safe_eval(self.encrypt_password,
                                             {'object': obj, 'time': time})
            except ValueError:
                raise ValidationError(
                    _("Python code used for encryption password is invalid.\n%s")
                    % self.encrypt_password)
        return encrypt_password

    def _encrypt_pdf(self, data, password):
        if not password:
            return data
        output_pdf = PdfFileWriter()
        in_buff = BytesIO(data)
        pdf = PdfFileReader(in_buff)
        output_pdf.appendPagesFromReader(pdf)
        output_pdf.encrypt(password)
        buff = BytesIO()
        output_pdf.write(buff)
        return buff.getvalue()
