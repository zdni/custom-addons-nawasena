{
    'name': 'Payment Request',
    'version': '1.0',
    'author': 'CV. TechnoIndo',
    'summary': 'Manage Payment Request',
    'description': """
This module contains all the common features of Payment Request
    """,
    'category': 'Payment',
    'website': 'http://www.technoindo.com',
    'depends': ['base', 'account'],
    'data': [
        'data/ir_sequence_data.xml',
        'security/ir.model.access.csv',
        
        'reports/report.xml',
        'reports/payment_request_report.xml',
        
        'views/menu.xml',
        'views/payment_request_views.xml',
    ],
    'images': ['static/description/icon.png'],
    'installable': True,
    'application': True,
}