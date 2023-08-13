{
    'name': 'Payment Request for Expenses',
    'version': '1.0',
    'author': 'CV. TechnoIndo',
    'summary': 'Manage Payment Request for Expenses',
    'description': """
This module contains all the common features of Payment Request for Expenses
    """,
    'category': 'Payment',
    'website': 'http://www.technoindo.com',
    'depends': ['base', 'hr_expense', 'payment_request'],
    'data': [
        'security/ir.model.access.csv',
        
        'reports/report.xml',
        'reports/pr_expenses_report.xml',
        
        'views/payment_request_views.xml',
    ],
    'installable': True,
    'application': True,
}