{
    'name': 'Custom Data Vehicles',
    'version': '1.0',
    'author': 'CV. TechnoIndo',
    'summary': 'Manage Custom Data Vehicles',
    'description': "Manage Custom Data Vehicles",
    'category': 'Employees',
    'website': 'http://www.technoindo.com',
    'depends': ['base', 'fleet', 'stock'],
    'data': [
        'security/ir.model.access.csv',
        
        'reports/fleet_license_template.xml',

        'wizards/fleet_license_wizard.xml',

        'views/fleet_vehicle_views.xml',
        'views/product_template_views.xml',
        'views/res_partner_views.xml',
    ],
    'installable': True,
    'application': False,
}