{
    'name': 'Payment Request for Vendor Bills',
    'version': '1.0',
    'author': 'CV. TechnoIndo',
    'summary': 'Manage Payment Request for Vendor Bills',
    'description': """
This module contains all the common features of Payment Request for Vendor Bills
    """,
    'category': 'Payment',
    'website': 'http://www.technoindo.com',
    'depends': ['base', 'account', 'payment_request', 'report_xlsx'],
    'data': [
        'security/ir.model.access.csv',
        
        'reports/report.xml',
        'reports/report_payment_request.xml',
        
        'views/payment_request_views.xml',

        'wizards/pr_acc_inv_wizard.xml',
    ],
    'installable': True,
    'application': True,
}