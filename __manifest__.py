{
    'name': 'Fee Driver',
    'version': '1.0',
    'author': 'CV. TechnoIndo',
    'summary': 'Custom Module Fee Driver',
    'description': "Custom Module Fee Driver in Sale Order",
    'category': 'Payment',
    'website': 'http://www.technoindo.com',
    'depends': ['base', 'custom_delivery', 'payment_request'],
    'data': [
        'reports/report_fee_driver_template.xml',
        'reports/report_payment_request_template.xml',
        'reports/report.xml',
        
        'security/ir.model.access.csv',
        
        'views/fee_driver_views.xml',
        'views/pr_fee_views.xml',
        'views/res_config_settings_views.xml',
    ],
    'installable': True,
    'application': False,
}