{
    'name': 'Custom Delivery',
    'version': '1.0',
    'author': 'CV. TechnoIndo',
    'summary': 'Custom Module Delivery Order',
    'description': "Custom Module Delivery Order in Transporter Company",
    'category': 'Sales',
    'website': 'http://www.technoindo.com',
    'depends': ['base', 'sale', 'custom_customer', 'custom_fleet', 'report_xlsx'],
    'data': [
        'data/ir_sequence_data.xml',
        
        'reports/report_handover_delivery_template.xml',
        'reports/report_tank_handover_template.xml',
        'reports/report_travel_doc_template.xml',
        'reports/sale_report.xml',
        
        'security/ir.model.access.csv',
        
        'views/change_vehicle_views.xml',
        'views/delivery_driver_views.xml',
        'views/fleet_vehicle_views.xml',
        'views/handover_conditions_views.xml',
        'views/product_views.xml',
        'views/res_config_settings_views.xml',
        'views/sale_order_views.xml',
        'views/seal_number_views.xml',
        'views/tank_handover_views.xml',
      
        'wizards/change_vehicle_wizard.xml',
        'wizards/delivery_driver_wizard.xml',
        'wizards/seal_number_wizard.xml',
        'wizards/tank_handover_wizard.xml'
    ],
    'installable': True,
    'application': False,
}