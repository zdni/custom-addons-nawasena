{
    'name': 'Custom Report Purchase',
    'version': '1.0',
    'author': 'CV. TechnoIndo',
    'summary': 'Custom Module Report Purchase',
    'description': "Custom Module Report Purchase",
    'category': 'Sales',
    'website': 'http://www.technoindo.com',
    'depends': ['base', 'purchase', 'report_xlsx'],
    'data': [
        'reports/report.xml',
        'wizards/report_purchase_wizard.xml',
    ],
    'installable': True,
    'application': False,
}