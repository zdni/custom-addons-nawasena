{
    'name': 'Custom Purchase',
    'version': '1.0',
    'author': 'CV. TechnoIndo',
    'summary': 'Custom Purchase',
    'description': "Custom Purchase",
    'category': 'Purchases',
    'website': 'http://www.technoindo.com',
    'depends': ['base', 'purchase'],
    'data': [
        'reports/purchase_order_templates.xml',
        'views/purchase_views.xml',
    ],
    'installable': True,
    'application': False,
}