{
    'name': 'Custom Data Customer',
    'version': '1.0',
    'author': 'CV. TechnoIndo',
    'summary': 'Manage Custom Data Customer',
    'description': "Manage Custom Data Customer",
    'category': 'Employees',
    'website': 'http://www.technoindo.com',
    'depends': ['base', 'sale', 'custom_fleet'],
    'data': [
        'security/ir.model.access.csv',
        'views/product_pricelist_views.xml',
        'views/res_partner_views.xml',
        'views/sale_setting_views.xml',
    ],
    'installable': True,
    'application': False,
}