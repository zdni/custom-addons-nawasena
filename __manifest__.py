{
    'name': 'Report Invoice',
    'version': '1.0',
    'author': 'CV. TechnoIndo',
    'summary': 'Custom Module Report Invoice',
    'description': "Custom Module Report Invoice per Customer",
    'category': 'Report',
    'website': 'http://www.technoindo.com',
    'depends': ['base', 'account', 'report_xlsx'],
    'data': [
        'reports/report_invoice_customer_template.xml',
        'reports/report.xml',
        
        'wizards/report_invoice_customer_wizard.xml'
    ],
    'installable': True,
    'application': False,
}