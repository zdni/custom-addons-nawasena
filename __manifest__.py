{
    'name': 'Installments Payment',
    'version': '1.0',
    'author': 'CV. TechnoIndo',
    'summary': 'Manage Installments Payment',
    'description': """
This module contains all the common features of Installments Payment
    """,
    'category': 'Installments',
    'website': 'http://www.technoindo.com',
    'depends': ['base', 'account', 'payment_request'],
    'data': [
        'data/ir_sequence_data.xml',
        
        'security/ir.model.access.csv',
        
        'reports/report.xml',
        'reports/installments_payment_report.xml',
        'reports/payment_request_report.xml',
        
        'views/installments_payment_views.xml',
        'views/payment_request_views.xml',
        'views/res_config_settings_views.xml',
    ],
    'images': ['static/description/icon.png'],
    'installable': True,
    'application': True,
}