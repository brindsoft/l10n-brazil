# -*- coding: utf-8 -*-
###############################################################################
#
# Copyright (C) 2012  Renato Lima - Akretion
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
###############################################################################

from openerp import models, fields, api
from openerp.addons import decimal_precision as dp

from openerp.addons.l10n_br_account.models.l10n_br_account import (
    L10nBrTaxDefinition,
    L10nBrTaxDefinitionTemplate
)
from openerp.addons.l10n_br_account.sped.ibpt.deolhonoimposto import (
    DeOlhoNoImposto,
    get_ibpt_product
)
from openerp.addons.l10n_br_base.tools.misc import punctuation_rm


class AccountProductFiscalClassificationTemplate(models.Model):
    _inherit = 'account.product.fiscal.classification.template'
    _rec_name = 'code'

    @api.multi
    @api.depends('purchase_tax_definition_line',
                 'sale_tax_definition_line')
    def _compute_taxes(self):
        for fc in self:
            fc.sale_tax_ids = [line.tax_template_id.id for line in
                               fc.sale_tax_definition_line]
            fc.purchase_tax_ids = [line.tax_template_id.id for line in
                                   fc.purchase_tax_definition_line]

    type = fields.Selection([('view', u'Visão'),
                             ('normal', 'Normal'),
                             ('extension', u'Extensão')],
                            string='Tipo',
                            default='normal')

    note = fields.Text(u'Observações')

    inv_copy_note = fields.Boolean(
        u'Copiar Observação',
        help=u"Copia a observação no documento fiscal")

    parent_id = fields.Many2one(
        'account.product.fiscal.classification.template',
        string='Parent Fiscal Classification',
        domain="[('type', 'in', ('view', 'normal'))]",
        ondelete='cascade')

    child_ids = fields.One2many(
        'account.product.fiscal.classification.template',
        'parent_id', string='Child Fiscal Classifications')

    sale_tax_definition_line = fields.One2many(
        'l10n_br_tax.definition.sale.template',
        'fiscal_classification_id', 'Taxes Definitions')

    sale_tax_ids = fields.Many2many(
        'account.tax.template', string='Sale Taxes',
        compute='_compute_taxes')

    purchase_tax_definition_line = fields.One2many(
        'l10n_br_tax.definition.purchase.template',
        'fiscal_classification_id', 'Taxes Definitions')

    purchase_tax_ids = fields.Many2many(
        'account.tax.template', string='Purchase Taxes',
        compute='_compute_taxes')

    tax_estimate_ids = fields.One2many(
        comodel_name='l10n_br_tax.estimate.template',
        inverse_name='fiscal_classification_id',
        string=u'Impostos Estimados')

    _sql_constraints = [
        ('account_fiscal_classfication_code_uniq', 'unique (code)',
         u'Já existe um classificação fiscal com esse código!')]

    cest = fields.Char(
        string='CEST',
        size=9,
        help=u"Código Especificador da Substituição Tributária ")


class L10nBrTaxDefinitionTemplateModel(L10nBrTaxDefinitionTemplate):
    """Model for tax definition template"""

    fiscal_classification_id = fields.Many2one(
        'account.product.fiscal.classification.template',
        'Fiscal Classification', select=True)
    tax_ipi_guideline_id = fields.Many2one(
        'l10n_br_account_product.ipi_guideline', string=u'Enquadramento IPI')
    tax_icms_relief_id = fields.Many2one(
        'l10n_br_account_product.icms_relief', string=u'Desoneração ICMS')

    _sql_constraints = [
        ('l10n_br_tax_definition_template_tax_template_id_uniq', 'unique \
         (tax_template_id, fiscal_classification_id)',
         u'Imposto já existente nesta classificação fiscal!')
    ]


class L10nBrTaxDefinitionSaleTemplate(L10nBrTaxDefinitionTemplateModel,
                                      models.Model):
    """Definition a class model for sales tax and tax code template"""
    _name = 'l10n_br_tax.definition.sale.template'


class L10nBrTaxDefinitionPurchaseTemplate(L10nBrTaxDefinitionTemplateModel,
                                          models.Model):
    """Definition a class model for purchase tax and tax code template"""
    _name = 'l10n_br_tax.definition.purchase.template'


class L10nBrTaxEstimateModel(models.AbstractModel):
    _name = 'l10n_br_tax.estimate.model'
    _auto = False

    active = fields.Boolean('Ativo', default=True)

    state_id = fields.Many2one(
        'res.country.state', 'Estado', required=True)

    federal_taxes_national = fields.Float(
        'Impostos Federais Nacional', default=0.00,
        digits_compute=dp.get_precision('Account'))

    federal_taxes_import = fields.Float(
        'Impostos Federais Importado', default=0.00,
        digits_compute=dp.get_precision('Account'))

    state_taxes = fields.Float(
        'Impostos Estaduais Nacional', default=0.00,
        digits_compute=dp.get_precision('Account'))

    municipal_taxes = fields.Float(
        'Impostos Municipais Nacional', default=0.00,
        digits_compute=dp.get_precision('Account'))

    date_start = fields.Date('Data Inicial')

    date_end = fields.Date('Data Final')

    key = fields.Char('Chave', size=32)

    version = fields.Char(u'Versão', size=32)

    origin = fields.Char('Fonte', size=32)


class L10nBrTaxEstimateTemplate(models.Model):
    _name = 'l10n_br_tax.estimate.template'
    _inherit = 'l10n_br_tax.estimate.model'

    fiscal_classification_id = fields.Many2one(
        'account.product.fiscal.classification.template',
        'Fiscal Classification', select=True)


class AccountProductFiscalClassification(models.Model):
    _inherit = 'account.product.fiscal.classification'
    _rec_name = 'code'

    @api.multi
    @api.depends('purchase_tax_definition_line',
                 'sale_tax_definition_line')
    def _compute_taxes(self):
        for fc in self:
            fc.sale_tax_ids = [line.tax_id.id for line in
                               fc.sale_tax_definition_line]
            fc.purchase_tax_ids = [line.tax_id.id for line in
                                   fc.purchase_tax_definition_line]

    type = fields.Selection([('view', u'Visão'),
                             ('normal', 'Normal'),
                             ('extension', u'Extensão')], 'Tipo',
                            default='normal')

    note = fields.Text(u'Observações')

    inv_copy_note = fields.Boolean(
        u'Copiar Observação',
        help=u"Copia a observação no documento fiscal")

    parent_id = fields.Many2one(
        'account.product.fiscal.classification',
        'Parent Fiscal Classification',
        domain="[('type', 'in', ('view', 'normal'))]", select=True)

    child_ids = fields.One2many(
        'account.product.fiscal.classification', 'parent_id',
        'Child Fiscal Classifications')

    sale_tax_definition_line = fields.One2many(
        'l10n_br_tax.definition.sale',
        'fiscal_classification_id', 'Taxes Definitions')

    sale_tax_ids = fields.Many2many(
        'account.tax', string='Sale Taxes',
        compute='_compute_taxes', store=True)

    purchase_tax_definition_line = fields.One2many(
        'l10n_br_tax.definition.purchase', 'fiscal_classification_id',
        'Taxes Definitions')

    purchase_tax_ids = fields.Many2many(
        'account.tax', string='Purchase Taxes',
        compute='_compute_taxes', store=True)

    tax_estimate_ids = fields.One2many(
        comodel_name='l10n_br_tax.estimate',
        inverse_name='fiscal_classification_id',
        string=u'Impostos Estimados')

    cest = fields.Char(
        string='CEST',
        size=9,
        help=u"Código Especificador da Substituição Tributária ")
    _sql_constraints = [
        ('account_fiscal_classfication_code_uniq', 'unique (code)',
         u'Já existe um classificação fiscal com esse código!')]

    @api.multi
    def get_ibpt(self):
        for item in self:
            brazil = item.env['res.country'].search([('code', '=', 'BR')])
            states = item.env['res.country.state'].search([('country_id', '=',
                                                            brazil.id)])
            company = item.company_id or item.env.user.company_id
            config = DeOlhoNoImposto(company.ipbt_token,
                                     punctuation_rm(company.cnpj_cpf),
                                     company.state_id.code)
            tax_estimate = item.env['l10n_br_tax.estimate']
            for state in states:
                result = get_ibpt_product(
                    config,
                    punctuation_rm(item.code or ''),
                    ex='0')
                update = tax_estimate.search([('state_id', '=', state.id),
                                              ('origin', '=', 'IBPT-WS'),
                                              ('fiscal_classification_id',
                                               '=', item.id)])
                vals = {
                    'fiscal_classification_id': item.id,
                    'origin': 'IBPT-WS',
                    'state_id': state.id,
                    'state_taxes': result.estadual,
                    'federal_taxes_national': result.nacional,
                    'federal_taxes_import': result.importado,
                    }
                if update:
                    update.write(vals)
                else:
                    tax_estimate.create(vals)
        return True


class L10nBrTaxDefinitionModel(L10nBrTaxDefinition):
    _name = 'l10n_br_tax.definition.model'

    fiscal_classification_id = fields.Many2one(
        'account.product.fiscal.classification',
        'Parent Fiscal Classification', select=True)
    tax_ipi_guideline_id = fields.Many2one(
        'l10n_br_account_product.ipi_guideline', string=u'Enquadramento IPI')
    tax_icms_relief_id = fields.Many2one(
        'l10n_br_account_product.icms_relief', string=u'Desoneração ICMS')

    _sql_constraints = [
        ('l10n_br_tax_definition_tax_id_uniq', 'unique (tax_id,\
        fiscal_classification_id)',
         u'Imposto já existente nesta classificação fiscal!')
    ]


class L10nBrTaxDefinitionSale(L10nBrTaxDefinitionModel, models.Model):
    _name = 'l10n_br_tax.definition.sale'


class L10nBrTaxDefinitionPurchase(L10nBrTaxDefinitionModel, models.Model):
    _name = 'l10n_br_tax.definition.purchase'


class L10nBrTaxEstimate(models.Model):
    _name = 'l10n_br_tax.estimate'
    _inherit = 'l10n_br_tax.estimate.model'

    fiscal_classification_id = fields.Many2one(
        'account.product.fiscal.classification',
        'Fiscal Classification', select=True)


class WizardAccountProductFiscalClassification(models.TransientModel):
    _inherit = 'wizard.account.product.fiscal.classification'

    @api.multi
    def action_create(self):
        obj_tax = self.env['account.tax']
        obj_tax_code = self.env['account.tax.code']
        obj_tax_code_template = self.env['account.tax.code.template']
        obj_tax_template = self.env['account.tax.template']
        obj_fc = self.env['account.product.fiscal.classification']
        obj_tax_purchase = self.env['l10n_br_tax.definition.purchase']
        obj_tax_sale = self.env['l10n_br_tax.definition.sale']

        obj_fc_template = self.env[
            'account.product.fiscal.classification.template']

        def map_taxes_codes(tax_definition, tax_type='sale'):
            for line in tax_definition:

                for company in companies:

                    if company_taxes[company].get(line.tax_template_id.id):

                        tax_def_domain = [
                            ('tax_id', '=', company_taxes[
                                company].get(line.tax_template_id.id)),
                            ('fiscal_classification_id', '=', fc_id.id),
                            ('company_id', '=', company)]

                        if tax_type == 'sale':
                            obj_tax_def = obj_tax_sale
                        else:
                            obj_tax_def = obj_tax_purchase

                        tax_def_result = obj_tax_def.search(tax_def_domain)

                        values = {
                            'tax_id': company_taxes[company].get(
                                line.tax_template_id.id),
                            'tax_code_id': company_codes[company].get(
                                line.tax_code_template_id.id),
                            'company_id': company,
                            'fiscal_classification_id': fc_id.id,
                        }

                        if tax_def_result:
                            tax_def_result.write(values)
                        else:
                            obj_tax_def.create(values)
            return True

        company_id = self.company_id.id
        companies = []

        if company_id:
            companies.append(company_id)
        else:
            companies = self.env['res.company'].sudo().search([]).ids

        company_taxes = {}
        company_codes = {}
        for company in companies:
            company_taxes[company] = {}
            company_codes[company] = {}
            for tax in obj_tax.sudo().search([('company_id', '=', company)]):
                tax_template = obj_tax_template.search(
                    [('name', '=', tax.name)])

                if tax_template:
                    company_taxes[company][tax_template[0].id] = tax.id

            for code in obj_tax_code.sudo().search(
                    [('company_id', '=', company)]):

                code_template = obj_tax_code_template.search(
                    [('name', '=', code.name)])

                if code_template:
                    company_codes[company][code_template[0].id] = code.id

        for fc_template in obj_fc_template.search([]):

            fc_id = obj_fc.search([('name', '=', fc_template.name)])

            if not fc_id:

                vals = {
                    'active': fc_template.active,
                    'code': fc_template.code,
                    'name': fc_template.name,
                    'description': fc_template.description,
                    'company_id': company_id,
                    'type': fc_template.type,
                    'note': fc_template.note,
                    'inv_copy_note': fc_template.inv_copy_note,
                }
                fc_id = obj_fc.sudo().create(vals)

            map_taxes_codes(fc_template.sale_tax_definition_line,
                            'sale')

            map_taxes_codes(fc_template.purchase_tax_definition_line,
                            'purchase')

        return True
