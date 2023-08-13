{
    'name': 'Report Transport',
    'version': '1.0',
    'author': 'CV. TechnoIndo',
    'summary': 'Custom Module Report Transport',
    'description': "Custom Module Report Transport in Transporter Company",
    'category': 'Sales',
    'website': 'http://www.technoindo.com',
    'depends': ['base', 'custom_delivery', 'report_xlsx'],
    'data': [
        'reports/report_transport_template.xml',
        'reports/report.xml',
        
        'wizards/report_transport_wizard.xml',
    ],
    'installable': True,
    'application': False,
}