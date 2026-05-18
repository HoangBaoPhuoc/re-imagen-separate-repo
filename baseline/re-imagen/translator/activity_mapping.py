ACTIVITY_MAPPINGS = {
    'Windows 10 Home - Single User': {
        'computer_on': {
            'mode': 'sequential',
            'commands': ['start_computer', 'login_single_user']
        },
        'computer_off': {
            'mode': 'sequential',
            'commands': ['shutdown_via_menu']
        },
        'google_search': {
            'mode': 'conditional',
            'commands': [
                'firefox_simple_initial_google_search_session',
                'firefox_simple_followup_google_search_session',
                'firefox_open_new_tab_and_search'
            ]
        },
        'create_text_document': {
            'mode': 'sequential',
            'commands': [
                'notepad_create_document'
            ]
        }
    }
}

        # It might make sense to layer the mapping a bit more to allow for shared functions between similar systems
